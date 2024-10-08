@echo off
setlocal

rem Capture the Poetry environment path
for /f "delims=" %%i in ('poetry env info --path') do set venv_path=%%i

rem Construct the site-packages path
set site_packages=%venv_path%\Lib\site-packages

rem Convert the path to forward slashes for Nuitka compatibility
set site_packages=%site_packages:\=/%

rem Initialize SIGNED_FLAG to 0 (unsigned by default)
set SIGNED_FLAG=0

rem Loop through the arguments and check if --signed is present
for %%a in (%*) do (
    if "%%a"=="--signed" (
        set SIGNED_FLAG=1
    )
)

rem Set the UAC_FLAG conditionally based on --signed flag
set UAC_FLAG=
if %SIGNED_FLAG%==1 (
    set UAC_FLAG=--windows-uac-uiaccess
)


rem Capture the Python version from the Poetry environment
for /f "delims=" %%v in ('poetry run python -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')"') do set python_version=%%v

rem Echo the constructed site-packages path and Python version for debugging
echo Site packages path: %site_packages%
echo Python version: %python_version%

rem Compile with Nuitka
poetry run python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-icon-from-ico=assets/images/icon.ico ^
    %UAC_FLAG% ^
    --output-dir=dist ^
    --enable-plugin=tk-inter ^
    --nofollow-import-to=unittest ^
    --nofollow-import-to=setuptools ^
    --include-data-dir=assets=assets ^
    --include-data-dir=configs=configs ^
    --include-data-dir="%site_packages%/mediapipe/modules=mediapipe/modules" ^
    --include-package=mediapipe ^
    --include-data-file="%site_packages%/mediapipe/python/_framework_bindings.cp%python_version%-win_amd64.pyd=mediapipe/python/_framework_bindings.cp%python_version%-win_amd64.pyd" ^
    --include-module=comtypes ^
    --include-module=comtypes.stream ^
    --include-module=comtypes.client ^
    --assume-yes-for-downloads ^
    FaceCommander.py

endlocal
