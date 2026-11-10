"""Belépési pont az .exe-hez.

Elindítja a Streamlit alkalmazást (app.py), hogy PyInstallerrel csomagolva,
Python telepítése nélkül is futtatható legyen (lásd PKG-01).
"""

import os
import sys

from streamlit.web import cli as stcli


def resource_path(relative: str) -> str:
    """Útvonal feloldása fejlesztői és PyInstaller (--onedir/--onefile) környezetben is."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def main() -> None:
    app_path = resource_path("app.py")
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
