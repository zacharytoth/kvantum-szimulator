import sys
from pathlib import Path
import customtkinter as ctk


def get_asset_path(filename: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets" / filename
    return Path(__file__).parent / "assets" / filename


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.geometry("500x300")
    app.title("BB84 Szimulátor Smoke Test")

    label = ctk.CTkLabel(
        app,
        text="BB84 Simulator - CustomTkinter OK",
        font=ctk.CTkFont(size=18, weight="bold"),
    )
    label.pack(expand=True)

    app.mainloop()


if __name__ == "__main__":
    main()