import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import random
from src.core import (
    init_database,
    agregar_ejercicio,
    eliminar_ejercicio,
    obtener_ejercicios_por_dificultad,
    contar_por_dificultad,
    generar_pdf_ejercicios,
    Ejercicio,
    ConfiguracionPDF,
    ConfiguracionDocumento,
)
from src.gui.vistas import VistaGenerar, VistaBanco, VistaEstadisticas
from src.gui.dialogs import DialogoAgregarEjercicio, DialogoVistaPrevia
from src.gui.widgets import DialogoProgresoPDF

VISTAS = {
    "generar": VistaGenerar,
    "banco": VistaBanco,
    "stats": VistaEstadisticas,
}
OPCIONES_NAV = [
    ("generar", "🎲 Generar PDF"),
    ("banco", "📚 Banco de Ejercicios"),
    ("stats", "📊 Estadísticas"),
]


class MainWindow(ctk.CTk):
    """Ventana principal: barra lateral de navegación + vistas apiladas."""

    def __init__(self):
        super().__init__()
        self.title("Generador de Ejercicios PDF")
        self.geometry("1100x750")
        self.minsize(900, 600)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        init_database()

        self.config_ultima = ConfiguracionPDF()
        self.config_documento = ConfiguracionDocumento()
        self.vistas: dict = {}
        self.nav_buttons: dict = {}

        self._crear_sidebar()
        self._crear_contenido()
        self.mostrar_vista("generar")

        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _cerrar(self):
        self.destroy()

    # ==================== ESTRUCTURA ====================
    def _crear_sidebar(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=225, corner_radius=0, fg_color="#1a1a2e")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar, text="📝 Generador", font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).grid(row=0, column=0, pady=(30, 4))

        ctk.CTkLabel(
            sidebar, text="Ejercicios PDF", font=ctk.CTkFont(size=12),
            text_color="#a0a0b0"
        ).grid(row=1, column=0, pady=(0, 30))

        for i, (key, texto) in enumerate(OPCIONES_NAV):
            btn = ctk.CTkButton(
                sidebar,
                text=texto,
                anchor="w",
                height=45,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#2a2a4a",
                text_color="white",
                font=ctk.CTkFont(size=14),
                command=lambda k=key: self.mostrar_vista(k),
            )
            btn.grid(row=i + 2, column=0, padx=15, pady=6, sticky="ew")
            self.nav_buttons[key] = btn

        ctk.CTkLabel(
            sidebar, text="© Angel Fabiano Salas Zapata",
            font=ctk.CTkFont(size=11), text_color="#666680"
        ).grid(row=10, column=0, pady=20, sticky="s")

    def _crear_contenido(self):
        self.container = ctk.CTkFrame(self, fg_color="#f4f6f9", corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

    def mostrar_vista(self, key: str):
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color="#2e86de", hover_color="#2874c4")
            else:
                btn.configure(fg_color="transparent", hover_color="#2a2a4a")

        if key not in self.vistas:
            self.vistas[key] = VISTAS[key](self.container, self)

        for vista in self.vistas.values():
            vista.grid(row=0, column=0, sticky="nsew")

        self.vistas[key].tkraise()
        self.vistas[key].on_mostrar()

    # ==================== ACCIONES COMPARTIDAS ====================
    def abrir_dialogo_agregar(self):
        DialogoAgregarEjercicio(self, on_guardar=self._guardar_ejercicio)

    def _guardar_ejercicio(self, nombre: str, dificultad: str, imagen: bytes):
        agregar_ejercicio(nombre, dificultad, imagen)
        self._refrescar_banco()
        messagebox.showinfo(
            "Ejercicio agregado", f"'{nombre}' se agregó correctamente al banco", parent=self
        )

    def ver_ejercicio(self, ejercicio: Ejercicio):
        DialogoVistaPrevia(self, ejercicio)

    def eliminar_ejercicio(self, ejercicio_id: int):
        if messagebox.askyesno(
            "Confirmar eliminación",
            "¿Está seguro de eliminar este ejercicio?", parent=self
        ):
            eliminar_ejercicio(ejercicio_id)
            self._refrescar_banco()

    def _refrescar_banco(self):
        vista = self.vistas.get("banco")
        if vista is not None:
            vista.refrescar()

    # ==================== GENERACIÓN DE PDF (HILO SEPARADO) ====================
    def generar_pdf(self, config: ConfiguracionPDF, documento: ConfiguracionDocumento = None):
        self.config_ultima = config
        if documento is None:
            documento = ConfiguracionDocumento()
        self.config_documento = documento

        ruta = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar PDF",
            defaultextension=".pdf",
            initialfile="ejercicios_generados.pdf",
            filetypes=[("Documento PDF", "*.pdf")],
        )
        if not ruta:
            return

        if not self._verificar_disponibilidad(config):
            return

        dialogo = DialogoProgresoPDF(self)

        def trabajo():
            try:
                todas = []
                etapas = [
                    ("Básico", config.basicos, 0.2),
                    ("Intermedio", config.intermedios, 0.45),
                    ("Difícil", config.dificiles, 0.7),
                ]
                for dificultad, cantidad, progreso in etapas:
                    if cantidad > 0:
                        dialogo.actualizar_seguro(
                            f"Seleccionando ejercicios {dificultad}...", progreso
                        )
                        todas.extend(
                            obtener_ejercicios_por_dificultad(dificultad, cantidad)
                        )

                if not todas:
                    dialogo.finalizar_seguro("error", "No hay ejercicios disponibles")
                    return

                random.shuffle(todas)
                dialogo.actualizar_seguro("Construyendo documento PDF...", 0.85)
                generar_pdf_ejercicios(todas, ruta, documento)

                dialogo.finalizar_seguro("exito", ruta)
            except Exception as e:
                dialogo.finalizar_seguro("error", str(e))

        threading.Thread(target=trabajo, daemon=True, name="GeneradorPDF").start()

    def _verificar_disponibilidad(self, config: ConfiguracionPDF) -> bool:
        conteo = contar_por_dificultad()
        faltantes = []
        for dificultad, cantidad in [
            ("Básico", config.basicos),
            ("Intermedio", config.intermedios),
            ("Difícil", config.dificiles),
        ]:
            if cantidad > 0:
                disponibles = conteo.get(dificultad, 0)
                if disponibles < cantidad:
                    faltantes.append(f"  • {dificultad}: disponibles {disponibles} / pedidos {cantidad}")

        if not faltantes:
            return True

        mensaje = (
            "No hay suficientes ejercicios en el banco:\n\n"
            + "\n".join(faltantes)
            + "\n\n¿Generar con los disponibles?"
        )
        return messagebox.askyesno("Ejercicios insuficientes", mensaje, parent=self)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()