import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import io
from typing import Callable
from src.core.models import Ejercicio, DIFICULTADES, DIFICULTAD_COLORES, DIFICULTAD_FONDOS
from src.gui.widgets import SelectorArchivoImagen


class DialogoAgregarEjercicio(ctk.CTkToplevel):
    """Diálogo modal para agregar un nuevo ejercicio al banco."""

    def __init__(self, master, on_guardar: Callable[[str, str, bytes], None]):
        super().__init__(master)
        self.title("Agregar Ejercicio")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.on_guardar = on_guardar

        self.geometry("460x540")
        self._centrar()
        self._crear_ui()

    def _centrar(self):
        self.update_idletasks()
        x = self.master.winfo_rootx() + (self.master.winfo_width() - 460) // 2
        y = self.master.winfo_rooty() + (self.master.winfo_height() - 540) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _crear_ui(self):
        main = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            main, text="➕ Nuevo Ejercicio", font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20))

        ctk.CTkLabel(main, text="Nombre:", font=ctk.CTkFont(size=13), anchor="w").grid(
            row=1, column=0, sticky="ew", pady=(0, 5)
        )
        self.entry_nombre = ctk.CTkEntry(main, placeholder_text="Ej: Suma de fracciones")
        self.entry_nombre.grid(row=2, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(main, text="Dificultad:", font=ctk.CTkFont(size=13), anchor="w").grid(
            row=3, column=0, sticky="ew", pady=(0, 5)
        )
        self.combo_dificultad = ctk.CTkComboBox(main, values=DIFICULTADES, state="readonly")
        self.combo_dificultad.set("Básico")
        self.combo_dificultad.grid(row=4, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(main, text="Imagen:", font=ctk.CTkFont(size=13), anchor="w").grid(
            row=5, column=0, sticky="ew", pady=(0, 5)
        )
        self.selector_imagen = SelectorArchivoImagen(main, on_change=lambda _: None)
        self.selector_imagen.grid(row=6, column=0, sticky="ew", pady=(0, 20))

        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=7, column=0, sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="Cancelar", height=38,
            fg_color="gray", hover_color="#555", command=self.destroy
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Guardar", height=38, command=self._guardar
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ctk.CTkButton(
            main, text="✖ Cerrar", height=36,
            fg_color="#e74c3c", hover_color="#c0392b", command=self.destroy
        ).grid(row=8, column=0, sticky="e", pady=(20, 0))

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        dificultad = self.combo_dificultad.get()
        imagen = self.selector_imagen.obtener_imagen()

        if not nombre:
            messagebox.showwarning("Campo requerido", "Ingrese un nombre para el ejercicio", parent=self)
            return
        if not imagen:
            messagebox.showwarning("Campo requerido", "Seleccione una imagen", parent=self)
            return

        self.on_guardar(nombre, dificultad, imagen)
        self.destroy()


class DialogoVistaPrevia(ctk.CTkToplevel):
    """Diálogo modal para ver un ejercicio ampliado (modo galería)."""

    def __init__(self, master, ejercicio: Ejercicio):
        super().__init__(master)
        self.title(f"Vista Previa: {ejercicio.nombre}")
        self.geometry("640x560")
        self.transient(master)
        self.grab_set()
        self._centrar()
        self._crear_ui(ejercicio)

    def _centrar(self):
        self.update_idletasks()
        x = self.master.winfo_rootx() + (self.master.winfo_width() - 640) // 2
        y = self.master.winfo_rooty() + (self.master.winfo_height() - 560) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _crear_ui(self, ejercicio: Ejercicio):
        main = ctk.CTkScrollableFrame(self)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            main, text=ejercicio.nombre, font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, pady=(0, 12))

        diff_color = DIFICULTAD_COLORES.get(ejercicio.dificultad, "#95a5a6")
        diff_fondo = DIFICULTAD_FONDOS.get(ejercicio.dificultad, "#ecf0f1")
        ctk.CTkLabel(
            main, text=f"• {ejercicio.dificultad}",
            font=ctk.CTkFont(size=14),
            text_color=diff_color, fg_color=diff_fondo,
            corner_radius=6, padx=16, pady=6
        ).grid(row=1, column=0, pady=(0, 20))

        try:
            img = Image.open(io.BytesIO(ejercicio.imagen))
            max_w, max_h = 560, 400
            if img.width > max_w or img.height > max_h:
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.img_label = ctk.CTkLabel(main, image=ctk_img, text="")
            self.img_label.grid(row=2, column=0)
        except Exception:
            ctk.CTkLabel(
                main, text="❌ No se pudo cargar la imagen",
                font=ctk.CTkFont(size=14), text_color="red"
            ).grid(row=2, column=0, pady=50)

        ctk.CTkButton(
            main, text="✖ Cerrar", width=140, height=36,
            fg_color="#e74c3c", hover_color="#c0392b", command=self.destroy
        ).grid(row=3, column=0, pady=(20, 10))