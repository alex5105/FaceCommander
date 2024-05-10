# Face Commander
Control and move the pointer, and type, using head movements and facial
gestures.

# Warning
-   This software isn't intended for human life-critical decisions, nor for
    medical use.
-   This software works by recognising *face landmarks* only. Face landmarks
    don't provide facial recognition nor identification.
-   This software doesn't store any unique face representation.

# Download the installer
1.  Download the FaceCommander-Installer.exe from the
    [Release section](../../releases/).
2.  Install it.
3.  Run from your Windows shortcuts or desktop.


# Run the code on Windows
1.  Install Python 3.10 for Windows, from here for example.  
    [python.org/downloads/release/python-31011/](https://www.python.org/downloads/release/python-31011/)

2.  Create a Python virtual environment (venv).

        cd /path/where/you/cloned/FaceCommander
        python -m venv venv

3.  Install the required PIP modules into the venv.

        .\venv\Scripts\python.exe -m pip install --upgrade pip
        .\venv\Scripts\python.exe -m pip install -r .\requirements.txt

Run the application.

    .\venv\Scripts\python.exe face_commander.py

In case of difficulty or for details, see the [Developer guide](./developer.md).

# Configs
## Basic config

>[cursor.json](configs/default/cursor.json)  

|           |                                       |
|-----------|---------------------------------------|
| camera_id | Default camera index on your machine. |
| tracking_vert_idxs | Tracking points for controlling cursor ([see](assets/images/uv_unwrap_full.png)) |
| spd_up    | Cursor speed in the upward direction  |
| spd_down  | Cursor speed in downward direction    |
| spd_left  | Cursor speed in left direction        |
| spd_right | Cursor speed in right direction       |
| pointer_smooth | Amount of cursor smoothness           |
| shape_smooth | Reduces the flickering of the action  |
| tick_interval_ms | interval between each tick of the pipeline in milliseconds |
| hold_trigger_ms | Hold action trigger delay in milliseconds |
| rapid_fire_interval_ms | interval between each activation of the action in milliseconds |
| auto_play | Automatically begin playing when you launch the program |
| enable    | Enable cursor control                 |
| mouse_acceleration | Make the cursor move faster when the head moves quickly |
| use_transformation_matrix | Control cursor using head direction (tracking_vert_idxs will be ignored) |
 

## Keybinding configs
>[mouse_bindings.json](configs/default/mouse_bindings.json)  
>[keyboard_bindings.json](configs/default/keyboard_bindings.json) 

The config parameters for keybinding configuration are in this structure.
```
gesture_name: [device_name, action_name, threshold, trigger_type]
```


|              |                                                                                                                                                                                                                                                                                                                                                                                       |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| gesture_name | Face expression name, see the [list](src/shape_list.py#L16)                                                                                                                                                                                                                                                                                                                           |
| device_name  | "meta", "mouse", or "keyboard"                                                                                                                                                                                                                                                                                                                                                        |
| action_name  | name of the action e.g. "left" for mouse. <br/>e.g. "ctrl" for keyboard<br/> e.g. "pause" for meta                                                                                                                                                                                                                                                                                    |
| threshold    | The action trigger threshold has values ranging from 0.0 to 1.0.                                                                                                                                                                                                                                                                                                                      |
| trigger_type | "single" for a single trigger<br/> "hold" for ongoing action. <br/> "dynamic" for a mixture of single and hold. It first acts like single and after passing the amount of miliseconds from hold_trigger_ms like hold. Note: this is the default behaviour for mouse buttons<br/> "toggle" to switch an action on and off<br/>"rapid" trigger an action every "rapid_fire_interval_ms" |

# Attributions
Blink graphics in the user interface are based on
[Eye icons created by Kiranshastry - Flaticon](https://www.flaticon.com/free-icons/eye).

## Model used
MediaPipe Face Landmark Detection API [Task Guide](https://developers.google.com/mediapipe/solutions/vision/face_landmarker)  
[MediaPipe BlazeFace Model Card](https://storage.googleapis.com/mediapipe-assets/MediaPipe%20BlazeFace%20Model%20Card%20(Short%20Range).pdf)  
[MediaPipe FaceMesh Model Card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Face%20Mesh%20V2.pdf)  
[Mediapipe Blendshape V2 Model Card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Blendshape%20V2.pdf)  
