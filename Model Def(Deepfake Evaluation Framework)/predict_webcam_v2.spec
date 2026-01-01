# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['predict_webcam_v2.py'],
    pathex=[],
    binaries=[],
    datas=[('def_video_face_mnv2_compat.h5', '.'), ('haarcascade_frontalface_default.xml', '.')],
    hiddenimports=['pyttsx3'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='predict_webcam_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
