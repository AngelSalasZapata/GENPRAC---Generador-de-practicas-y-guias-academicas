import customtkinter as ctk
from typing import TYPE_CHECKING, Optional
from src.core import (
    obtener_ejercicios,
    ConfiguracionDocumento,
    ETIQUETAS_DOCUMENTO,
)

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow


class VistaGenerar(ctk.CTkFrame):
    """Vista 1: configuración y generación de PDF aleatorio con estilo Frutiger Aero."""

    def __init__(self, master, app: "MainWindow"):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._crear_ui()

    def on_mostrar(self):
        pass

    def _crear_ui(self):
        # Frutiger Aero: Banner celestial luminoso
        hero = ctk.CTkFrame(self, fg_color="#0284c7", corner_radius=14)
        hero.grid(row=0, column=0, padx=25, pady=(25, 20), sticky="ew")
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hero, text="🎲 Generar PDF Aleatorio",
            font=ctk.CTkFont(size=24, weight="bold"), text_color="#ffffff"
        ).grid(row=0, column=0, padx=25, pady=(22, 4), sticky="w")

        ctk.CTkLabel(
            hero, text="Configure la cantidad de ejercicios por dificultad y genere un documento PDF",
            font=ctk.CTkFont(size=13), text_color="#e0f2fe"
        ).grid(row=1, column=0, padx=25, pady=(0, 22), sticky="w")

        # Tarjeta principal blanca con borde suave celeste
        card = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=14, border_width=1, border_color="#d0e6f5")
        card.grid(row=1, column=0, padx=25, pady=(0, 25), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Configuración de Ejercicios",
            font=ctk.CTkFont(size=17, weight="bold"), text_color="#0c4a6e"
        ).grid(row=0, column=0, padx=35, pady=(28, 18), sticky="w")

        cfg = self.app.config_ultima
        filas = ctk.CTkFrame(card, fg_color="transparent")
        filas.grid(row=1, column=0, padx=35, sticky="ew")

        from src.gui.widgets import SpinboxNumerico
        self._spin_basicos = SpinboxNumerico(filas, "Básicos", 0, 60, cfg.basicos)
        self._spin_basicos.grid(row=0, column=0, pady=6, sticky="ew")
        self._spin_intermedios = SpinboxNumerico(filas, "Intermedios", 0, 60, cfg.intermedios)
        self._spin_intermedios.grid(row=1, column=0, pady=6, sticky="ew")
        self._spin_dificiles = SpinboxNumerico(filas, "Difíciles", 0, 60, cfg.dificiles)
        self._spin_dificiles.grid(row=2, column=0, pady=6, sticky="ew")

        for sp in [self._spin_basicos, self._spin_intermedios, self._spin_dificiles]:
            sp.entry.bind("<KeyRelease>", lambda e: self._actualizar_total())

        ctk.CTkFrame(card, height=1, fg_color="#e2e8f0").grid(
            row=2, column=0, padx=35, pady=(18, 16), sticky="ew"
        )

        ctk.CTkLabel(
            card, text="Personalizar Documento",
            font=ctk.CTkFont(size=17, weight="bold"), text_color="#0c4a6e"
        ).grid(row=3, column=0, padx=35, pady=(0, 14), sticky="w")

        doc = ctk.CTkFrame(card, fg_color="transparent")
        doc.grid(row=4, column=0, padx=35, sticky="ew")
        doc.grid_columnconfigure(0, weight=1)

        doc_cfg = self.app.config_documento
        ctk.CTkLabel(doc, text="Título:", font=ctk.CTkFont(size=13), text_color="#334155", anchor="w").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_titulo = ctk.CTkEntry(
            doc, placeholder_text="Ej: Examen de Matemáticas",
            border_color="#bae6fd"
        )
        self.entry_titulo.insert(0, doc_cfg.titulo)
        self.entry_titulo.grid(row=1, column=0, pady=(4, 10), sticky="ew")

        ctk.CTkLabel(doc, text="Autor:", font=ctk.CTkFont(size=13), text_color="#334155", anchor="w").grid(
            row=2, column=0, sticky="w"
        )
        self.entry_autor = ctk.CTkEntry(
            doc, placeholder_text="Ej: Nombre del profesor",
            border_color="#bae6fd"
        )
        self.entry_autor.insert(0, doc_cfg.autor)
        self.entry_autor.grid(row=3, column=0, pady=(4, 10), sticky="ew")

        ctk.CTkLabel(doc, text="Etiqueta de las imágenes:", font=ctk.CTkFont(size=13), text_color="#334155", anchor="w").grid(
            row=4, column=0, sticky="w"
        )
        self.combo_etiqueta = ctk.CTkComboBox(
            doc, values=ETIQUETAS_DOCUMENTO, height=36,
            button_color="#0284c7", button_hover_color="#0369a1"
        )
        self.combo_etiqueta.set(doc_cfg.etiqueta)
        self.combo_etiqueta.grid(row=5, column=0, pady=(4, 0), sticky="ew")

        ctk.CTkFrame(doc, height=1, fg_color="#e2e8f0").grid(
            row=6, column=0, pady=(14, 12), sticky="ew"
        )

        ctk.CTkLabel(
            doc, text="Espacio en blanco entre ejercicios:",
            font=ctk.CTkFont(size=13), text_color="#334155", anchor="w"
        ).grid(row=7, column=0, sticky="w")

        fila_espacio = ctk.CTkFrame(doc, fg_color="transparent")
        fila_espacio.grid(row=8, column=0, pady=(6, 0), sticky="ew")

        self.check_espacio = ctk.CTkCheckBox(
            fila_espacio, text="Agregar espacio", command=self._toggle_espacio,
            fg_color="#10b981", hover_color="#059669", text_color="#334155"
        )
        self.check_espacio.grid(row=0, column=0, padx=(0, 12), sticky="w")

        self.entry_espacio = ctk.CTkEntry(
            fila_espacio, width=80, justify="center", border_color="#bae6fd"
        )
        self.entry_espacio.insert(0, "2.0")
        self.entry_espacio.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(fila_espacio, text="cm", font=ctk.CTkFont(size=12), text_color="#64748b").grid(
            row=0, column=2, padx=(6, 0), sticky="w"
        )

        self._toggle_espacio()

        self.label_total = ctk.CTkLabel(
            card, text=f"📊 Total de ejercicios: {cfg.total}",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#0c4a6e"
        )
        self.label_total.grid(row=5, column=0, padx=35, pady=(24, 6), sticky="w")

        # Botón principal en verde Frutiger Aero vibrante
        ctk.CTkButton(
            card, text="🎲 Generar PDF Aleatorio",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50, corner_radius=10,
            fg_color="#10b981", hover_color="#059669", text_color="#ffffff",
            command=self._generar
        ).grid(row=6, column=0, padx=35, pady=(10, 30), sticky="ew")

    def _toggle_espacio(self):
        estado = "normal" if self.check_espacio.get() else "disabled"
        self.entry_espacio.configure(state=estado)

    def _actualizar_total(self):
        total = self._spin_basicos.obtener() + self._spin_intermedios.obtener() + self._spin_dificiles.obtener()
        self.label_total.configure(text=f"📊 Total de ejercicios: {total}")

    def _generar(self):
        import tkinter.messagebox as mb
        from src.core import ConfiguracionPDF, ConfiguracionDocumento
        config = ConfiguracionPDF(
            basicos=self._spin_basicos.obtener(),
            intermedios=self._spin_intermedios.obtener(),
            dificiles=self._spin_dificiles.obtener(),
        )
        if config.total == 0:
            mb.showwarning("Sin ejercicios", "Seleccione al menos 1 ejercicio", parent=self.app)
            return

        espacio = 0.0
        if self.check_espacio.get():
            try:
                espacio = max(0.0, float(self.entry_espacio.get().strip().replace(",", ".")))
            except ValueError:
                espacio = 0.0
                mb.showwarning(
                    "Valor inválido",
                    "El espacio en blanco debe ser un número en centímetros. Se usará 0 cm.",
                    parent=self.app,
                )

        por_defecto = ConfiguracionDocumento()
        documento = ConfiguracionDocumento(
            titulo=self.entry_titulo.get().strip() or por_defecto.titulo,
            autor=self.entry_autor.get().strip() or por_defecto.autor,
            etiqueta=self.combo_etiqueta.get().strip() or por_defecto.etiqueta,
            espacio_cm=espacio,
        )
        self.app.config_documento = documento
        self.app.generar_pdf(config, documento)


class VistaBanco(ctk.CTkFrame):
    """Vista 2: banco de ejercicios con búsqueda, filtro y galería estilo Frutiger Aero."""

    def __init__(self, master, app: "MainWindow"):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._cache_ejercicios: list = []
        self._tarea_filtro: Optional[str] = None
        self._crear_ui()
        self.refrescar()

    def on_mostrar(self):
        if getattr(self.app, "banco_requiere_recarga", True):
            self.refrescar()

    def _crear_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=25, pady=(25, 5), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="📚 Banco de Ejercicios",
            font=ctk.CTkFont(size=24, weight="bold"), text_color="#0c4a6e"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header, text="Agregue, revise y elimine ejercicios con sus imágenes",
            font=ctk.CTkFont(size=13), text_color="#64748b"
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Botón Cargar Varios (Verde esmeralda Frutiger Aero)
        ctk.CTkButton(
            header, text="🖼️ Cargar Varios",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40, fg_color="#10b981", hover_color="#059669", text_color="#ffffff",
            corner_radius=10,
            command=self.app.abrir_dialogo_carga_masiva
        ).grid(row=0, column=2, rowspan=2, padx=(0, 10), sticky="e")

        # Botón Agregar Ejercicio (Azul cielo Frutiger Aero)
        ctk.CTkButton(
            header, text="➕ Agregar Ejercicio",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40, fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            corner_radius=10,
            command=self.app.abrir_dialogo_agregar
        ).grid(row=0, column=1, rowspan=2, padx=10, sticky="e")

        # Barra de búsqueda y filtro blanca con borde suave
        toolbar = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12, border_width=1, border_color="#d0e6f5")
        toolbar.grid(row=1, column=0, padx=25, pady=(10, 5), sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)

        self.entry_busqueda = ctk.CTkEntry(
            toolbar, placeholder_text="🔍 Buscar por nombre...", height=36,
            border_color="#bae6fd"
        )
        self.entry_busqueda.grid(row=0, column=0, padx=(15, 10), pady=12, sticky="ew")
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self._programar_filtro())

        self.combo_dificultad = ctk.CTkComboBox(
            toolbar, values=["Todas", "Básico", "Intermedio", "Difícil"],
            state="readonly", width=160, height=36,
            button_color="#0284c7", button_hover_color="#0369a1"
        )
        self.combo_dificultad.set("Todas")
        self.combo_dificultad.configure(command=lambda _: self._programar_filtro())
        self.combo_dificultad.grid(row=0, column=1, padx=(10, 15), pady=12)

        self.label_conteo = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="#64748b"
        )
        self.label_conteo.grid(row=2, column=0, padx=30, pady=(0, 2), sticky="w")

        from src.gui.widgets import GaleriaEjercicios
        self.galeria = GaleriaEjercicios(
            self,
            on_ejercicio_click=self.app.ver_ejercicio,
            on_ejercicio_delete=self.app.eliminar_ejercicio,
        )
        self.galeria.grid(row=3, column=0, padx=25, pady=(8, 25), sticky="nsew")

    def refrescar(self):
        self._cancelar_filtro()
        self._cache_ejercicios = obtener_ejercicios()
        self.galeria.limpiar_cache()
        self._aplicar_filtro(reiniciar=True)
        self.app.banco_requiere_recarga = False

    def _programar_filtro(self, *_):
        self._cancelar_filtro()
        self._tarea_filtro = self.after(220, self._aplicar_filtro)

    def _cancelar_filtro(self):
        if self._tarea_filtro is not None:
            try:
                self.after_cancel(self._tarea_filtro)
            except Exception:
                pass
            self._tarea_filtro = None

    def _aplicar_filtro(self, reiniciar: bool = False):
        self._tarea_filtro = None
        todos = self._cache_ejercicios
        filtro = self.combo_dificultad.get()
        texto = self.entry_busqueda.get().strip().lower()

        ejercicios = [
            e for e in todos
            if (filtro == "Todas" or e.dificultad == filtro)
            and (not texto or texto in e.nombre.lower())
        ]

        if ejercicios:
            self.galeria.actualizar(ejercicios, reiniciar=reiniciar)
            self.label_conteo.configure(text=f"Mostrando {len(ejercicios)} de {len(todos)} ejercicios")
        else:
            self.galeria.mostrar_vacio("No se encontraron ejercicios\nAjuste la búsqueda o los filtros")
            self.label_conteo.configure(text=f"{len(todos)} ejercicios en total")
