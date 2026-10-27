"""
Lanzador de NetConfigSwitcher
Redirige a NetConfigSwitcher.py para asegurar compatibilidad total con el archivo original.
"""
import sys
import os

if __name__ == "__main__":
    from NetConfigSwitcher import NetConfigSwitcher, verify_admin_elevation
    import customtkinter as ctk

    verify_admin_elevation()
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = NetConfigSwitcher()
    app.mainloop()
