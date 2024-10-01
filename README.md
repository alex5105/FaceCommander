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

# Development Setup and Running the Application
## Prerequisites

1. **Install Python 3.10** (or higher) for Windows from the [official Python website](https://www.python.org/downloads/release/python-31011/).

2. **Install Poetry** if you don't have it already. You can install Poetry by running:

    ```sh
    curl -sSL https://install.python-poetry.org | python3 -
    ```

    Alternatively, on Windows, you can use:

    ```sh
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    ```

    Ensure that Poetry is available in your PATH. You can verify this by running:

    ```sh
    poetry --version
    ```

## Setting Up the Development Environment

1. **Clone the Repository** if you haven't already:

    ```sh
    git clone https://github.com/AceCentre/FaceCommander.git
    cd FaceCommander
    ```

2. **Create a Virtual Environment and Install Dependencies**:

    Poetry automatically handles virtual environments, so you don't need to manually create one. Simply run:

    ```sh
    poetry install
    ```

    This command will:
    
    - Create a virtual environment in the `.venv` directory within your project.
    - Install all dependencies listed in `pyproject.toml` and lock them in `poetry.lock`.

3. **Activate the Virtual Environment** (if needed):

    While Poetry typically handles this automatically, you can activate the virtual environment manually if required:

    ```sh
    poetry shell
    ```

## Running the Application

1. **Run the Application**:

    With the virtual environment active, you can run the application directly:

    ```sh
    poetry run python FaceCommander.py
    ```

    This ensures that the Python interpreter and dependencies used are from the Poetry-managed environment.

## Additional Tips

- **Adding Dependencies**: To add new dependencies, use:

    ```sh
    poetry add <package_name>
    ```

- **Updating Dependencies**: To update all dependencies to their latest versions (within the constraints defined):

    ```sh
    poetry update
    ```

- **Exiting the Virtual Environment**: To exit the Poetry shell (virtual environment), simply type:

    ```sh
    exit
    ```

## Troubleshooting

If you encounter any issues, refer to the [Developer Guide](./Developer/readme.md) for detailed instructions and troubleshooting tips.

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
