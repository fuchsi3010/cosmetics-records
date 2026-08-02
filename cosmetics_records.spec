# PyInstaller build: pyinstaller cosmetics_records.spec
import sys

a = Analysis(
    ["src/cosmetics_records/app.py"],
    pathex=["src"],
    datas=[
        (
            "src/cosmetics_records/resources/icons",
            "cosmetics_records/resources/icons",
        )
    ],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="CosmeticsRecords",
    console=False,
    icon=(
        "src/cosmetics_records/resources/icons/icon.ico"
        if sys.platform == "win32"
        else None
    ),
)
