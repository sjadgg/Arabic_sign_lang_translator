# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('model.onnx', '.'), ('scaler.joblib', '.'), ('label_encoder.joblib', '.')]
datas += collect_data_files('opencv-python')
datas += collect_data_files('mediapipe')
datas += collect_data_files('onnxruntime')


a = Analysis(
    ['aiapp2.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['winrt.windows.media.speechsynthesis', 'winrt.windows.storage.streams', 'winrt.windows.foundation', 'winrt.windows.foundation.collections', 'winsound', 'pythoncom'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PIL.plugins._avif', 'tensorflow'],
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
    name='Deaf Talk',
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
