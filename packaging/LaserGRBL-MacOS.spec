from pathlib import Path


project_root = Path(SPECPATH).resolve().parent

analysis = Analysis(
    [str(project_root / "packaging" / "entrypoint.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[],
    hiddenimports=["PyQt6.QtSerialPort"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="LaserGRBL for macOS",
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
)

collection = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LaserGRBL for macOS",
)

application = BUNDLE(
    collection,
    name="LaserGRBL for macOS.app",
    icon=str(project_root / "build" / "LaserGRBL.icns"),
    bundle_identifier="io.github.alexkypraiou.lasergrbl-macos",
    version="0.2.0",
    info_plist={
        "CFBundleDisplayName": "LaserGRBL for macOS",
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "MIT License",
    },
)
