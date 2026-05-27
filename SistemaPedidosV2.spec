# -*- mode: python ; coding: utf-8 -*-
# Build onedir dist/SistemaPedidosV2/ — tools/build_release.ps1

import os

_root = os.path.normpath(os.path.dirname(os.path.abspath(SPEC)))
_icon = os.path.join(_root, "assets", "logos", "logo_brasul.ico")
if not os.path.isfile(_icon):
    _icon = None

_bundle_datas = [
    ("assets", "assets"),
]
_db_dir = os.path.join(_root, "database")
if os.path.isdir(_db_dir):
    _bundle_datas.append((_db_dir, "database"))
try:
    import PySide6

    _pyside_tr = os.path.join(os.path.dirname(PySide6.__file__), "translations")
    if os.path.isdir(_pyside_tr):
        _bundle_datas.append((_pyside_tr, "PySide6/translations"))
except Exception:
    pass

a = Analysis(
    ["main.py"],
    pathex=[_root],
    binaries=[],
    datas=_bundle_datas,
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name="SistemaPedidosV2",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SistemaPedidosV2",
)
