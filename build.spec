# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

from pathlib import Path
import mediapipe
import customtkinter

block_cipher = None

mp_init = Path(mediapipe.__file__)
mp_modules =  Path(mp_init.parent,"modules")

ctk_init = Path(customtkinter.__file__)
ctk_modules =  Path(ctk_init.parent,"modules")

tkinterwebCollections = collect_all('tkinterweb')
app = Analysis(
    ['grimassist.py'],
    pathex=[],
    binaries=tkinterwebCollections[1],
    datas=[
        (mp_modules.as_posix(), 'mediapipe/modules')
        , ('assets','assets')
        , ('configs','configs')
        , (ctk_init.parent.as_posix(), 'customtkinter')
        , *tkinterwebCollections[0]
    ],
    hiddenimports=tkinterwebCollections[2],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_app = PYZ(app.pure, app.zipped_data, cipher=block_cipher)

exe_app = EXE(
    pyz_app,
    app.scripts,
    [],
    exclude_binaries=True,
    name='grimassist',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon='assets/images/icon.ico',
    codesign_identity=None,
    entitlements_file=None,
)


coll = COLLECT(
    exe_app,
    app.binaries,
    app.zipfiles,
    app.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='grimassist',
)
