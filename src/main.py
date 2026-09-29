import customtkinter as ctk
from src.core import init_database


def main():
    # Configurar apariencia
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Inicializar BD
    init_database()

    # Importar aquí para evitar circular imports
    from src.gui.main_window import MainWindow

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()