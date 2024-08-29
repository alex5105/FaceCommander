import logging
import time
from typing import Any

import mediapipe as mp
import numpy as np
import numpy.typing as npt
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark
from mediapipe.python._framework_bindings import image as mediapipe_image
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import FaceLandmarkerResult
from numpy import ndarray, dtype

import src.utils as utils
from src.config_manager import ConfigManager
from src.singleton_meta import Singleton

logger = logging.getLogger("FaceMesh")

MP_TASK_FILE = "assets/task/face_landmarker_with_blendshapes.task"

BLENDS_MAX_BUFFER = 100
N_SHAPES = 52
np.set_printoptions(precision=2, suppress=True)

class FaceMesh(metaclass=Singleton):

    def __init__(self):
        self.smooth_kernel = None
        logger.info("Initialize FaceMesh singleton")
        self.mp_landmarks = None
        self.tracking_location = None
        self.blendshapes_buffer = np.zeros([BLENDS_MAX_BUFFER, N_SHAPES])
        self.smooth_blendshapes = None
        self.model = None
        self.latest_time_ms = 0
        self.is_started = False

    def start(self):
        if not self.is_started:
            logger.info("Start FaceMesh singleton")
            # In Windows, needs to open buffer directly
            with open(MP_TASK_FILE, mode="rb") as f:
                f_buffer = f.read()
            base_options = python.BaseOptions(model_asset_buffer=f_buffer)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=True,
                output_facial_transformation_matrixes=True,
                running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
                num_faces=1,
                result_callback=self.mp_callback)
            self.model = vision.FaceLandmarker.create_from_options(options)

            self.calc_smooth_kernel()

    def calc_smooth_kernel(self):
        self.smooth_kernel = utils.calc_smooth_kernel(
            ConfigManager().config["shape_smooth"])

    def calculate_tracking_location(self, mp_result, use_transformation_matrix=False) -> ndarray[Any, dtype[Any]]:
        screen_w = ConfigManager().config["fix_width"]
        screen_h = ConfigManager().config["fix_height"]
        landmarks = mp_result.face_landmarks[0]

        if use_transformation_matrix:
            M = mp_result.facial_transformation_matrixes[0]
            U, _, V = np.linalg.svd(M[:3, :3])
            R = U @ V

            res = R @ np.array([0, 0, 1])

            x_pixel = (res[0] / 1) * 0.3
            y_pixel = (res[1] / 1) * 0.3

            x_pixel = screen_w / 2 + (x_pixel * screen_w / 2)
            y_pixel = screen_h / 2 - (y_pixel * screen_h / 2)

        else:
            axs = []
            ays = []

            for p in ConfigManager().config["tracking_vert_idxs"]:
                px = landmarks[p].x * screen_w
                py = landmarks[p].y * screen_h
                axs.append(px)
                ays.append(py)

            x_pixel = np.mean(axs)
            y_pixel = np.mean(ays)

        return np.array([x_pixel, y_pixel], np.float32)

    def mp_callback(self, mp_result: FaceLandmarkerResult, output_image: mediapipe_image.Image, timestamp_ms: int) -> None:
        if len(mp_result.face_landmarks) >= 1 and len(
                mp_result.face_blendshapes) >= 1:
            self.mp_landmarks = mp_result.face_landmarks[0]
            # Point for moving pointer
            self.tracking_location = self.calculate_tracking_location(
                mp_result,
                use_transformation_matrix=ConfigManager(
                ).config["use_transformation_matrix"])
            self.blendshapes_buffer = np.roll(self.blendshapes_buffer,
                                              shift=-1,
                                              axis=0)

            self.blendshapes_buffer[-1] = np.array(
                [b.score for b in mp_result.face_blendshapes[0]])
            self.smooth_blendshapes = utils.apply_smoothing(
                self.blendshapes_buffer, self.smooth_kernel)
            self.smooth_blendshapes[9] = self.detect_eye_blink_right()
            self.smooth_blendshapes[10] = self.detect_eye_blink_left()
            self.smooth_blendshapes[11] = self.detect_eye_blink()

        else:
            self.mp_landmarks = None
            self.tracking_location = None

    def detect_frame(self, frame_np: npt.ArrayLike):

        t_ms = int(time.time() * 1000)
        if t_ms <= self.latest_time_ms:
            return

        frame_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_np)
        self.model.detect_async(frame_mp, t_ms)
        self.latest_time_ms = t_ms

    def get_landmarks(self) -> list[NormalizedLandmark]:
        return self.mp_landmarks

    def get_tracking_location(self) -> ndarray:
        return self.tracking_location

    def get_blendshapes(self) -> npt.ArrayLike:  
        return self.smooth_blendshapes

    def detect_eye_blink_right(self):
        if self.mp_landmarks is None:
            return 0.0  # No landmarks detected, return 0 or similar default value

        # Define landmark indices for the right eye
        right_eye_landmarks = [self.mp_landmarks[362], self.mp_landmarks[263], self.mp_landmarks[386], self.mp_landmarks[374]]

        # Calculate EAR for right eye
        re_ratio = self.calculate_ear(right_eye_landmarks)
        return re_ratio
        
    def detect_eye_blink_left(self):
        if self.mp_landmarks is None:
            return 0.0  # No landmarks detected, return 0 or similar default value

        # Define landmark indices for the left eye
        left_eye_landmarks = [self.mp_landmarks[33], self.mp_landmarks[133], self.mp_landmarks[159], self.mp_landmarks[145]]

        # Calculate EAR for left eye
        le_ratio = self.calculate_ear(left_eye_landmarks)
        return le_ratio

    def detect_eye_blink(self):
        """Calculate EAR and determine if a blink is detected."""
        if self.mp_landmarks is None:
            return 0.0  # No landmarks detected, return 0 or similar default value

        # Define landmark indices for the eyes
        left_eye_landmarks = [self.mp_landmarks[33], self.mp_landmarks[133], self.mp_landmarks[159], self.mp_landmarks[145]]
        right_eye_landmarks = [self.mp_landmarks[362], self.mp_landmarks[263], self.mp_landmarks[386], self.mp_landmarks[374]]

        # Calculate EAR for both eyes
        re_ratio = self.calculate_ear(right_eye_landmarks)
        le_ratio = self.calculate_ear(left_eye_landmarks)

        # Combine EAR values (average or other logic)
        ear_value = (re_ratio + le_ratio) / 2
        
        return ear_value

    def calculate_ear(self, eye_landmarks):
        """Calculate the Eye Aspect Ratio (EAR) for an eye."""
        rw_distance = self.euclidean_distance(eye_landmarks[0], eye_landmarks[1])
        rh_distance = self.euclidean_distance(eye_landmarks[2], eye_landmarks[3])

        ear = rh_distance * 3 / rw_distance                
        ear = 1 - ear        
        if ear < 0:
            ear = 0
        
        return ear

    def euclidean_distance(self, point1, point2):
        """Calculate the Euclidean distance between two points."""
        return np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)

    def destroy(self):
        if self.model is not None:
            self.model.close()
        self.model = None
        self.mp_landmarks = None
        self.blendshapes_buffer = None
