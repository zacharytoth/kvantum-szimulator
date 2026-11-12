import sys
from pathlib import Path
import customtkinter as ctk
from gui import BB84App


def get_asset_path(filename: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets" / filename
    return Path(__file__).parent / "assets" / filename


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = BB84App()
    app.mainloop()

if __name__ == "__main__":
    main()