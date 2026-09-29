import customtkinter as ctk
from typing import TYPE_CHECKING
from src.core import (
    obtener_ejercicios,
    contar_por_dificultad,
    EstadisticasBanco,
    ConfiguracionDocumento,
    ETIQUETAS_DOCUMENTO,
)

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow

OBJETIVOS = {"Básico": 30, "Intermedio": 20, "Difícil": 10}
COLORES_DIF = {"Básico": "#27ae60", "Intermedio": "#f39c12", "Difícil": "#e74c3c"}


class VistaGenerar(ctk.CTkFrame):
    """Vista 1: configuración y generación de PDF aleatorio."""

    def __init__(self, master, app: "MainWindow"):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._crear_ui()

    def on_mostrar(self):
        pass

    def _crear_ui(self):
        hero = ctk.CTkFrame(self, fg_color="#2e86de", corner_radius=12)
        hero.grid(row=0, column=0, padx=25, pady=(25, 20), sticky="ew")
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hero, text="🎲 Generar PDF Aleatorio",
            font=ctk.CTkFont(size=24, weight="bold"), text_color="white"
        ).grid(row=0, column=0, padx=25, pady=(22, 4), sticky="w")

        ctk.CTkLabel(
            hero, text="Configure la cantidad de ejercicios por dificultad y genere un documento PDF",
            font=ctk.CTkFont(size=13), text_color="#dbe9fb"
        ).grid(row=1, column=0, padx=25, pady=(0, 22), sticky="w")

        card = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        card.grid(row=1, column=0, padx=25, pady=(0, 25), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Configuración de Ejercicios",
            font=ctk.CTkFont(size=17, weight="bold")
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

        ctk.CTkFrame(card, height=1, fg_color="#e0e0e0").grid(
            row=2, column=0, padx=35, pady=(18, 16), sticky="ew"
        )

        ctk.CTkLabel(
            card, text="Personalizar Documento",
            font=ctk.CTkFont(size=17, weight="bold")
        ).grid(row=3, column=0, padx=35, pady=(0, 14), sticky="w")

        doc = ctk.CTkFrame(card, fg_color="transparent")
        doc.grid(row=4, column=0, padx=35, sticky="ew")
        doc.grid_columnconfigure(0, weight=1)

        doc_cfg = self.app.config_documento
        ctk.CTkLabel(doc, text="Título:", font=ctk.CTkFont(size=13), anchor="w").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_titulo = ctk.CTkEntry(
            doc, placeholder_text="Ej: Examen de Matemáticas",
        )
        self.entry_titulo.insert(0, doc_cfg.titulo)
        self.entry_titulo.grid(row=1, column=0, pady=(4, 10), sticky="ew")

        ctk.CTkLabel(doc, text="Autor:", font=ctk.CTkFont(size=13), anchor="w").grid(
            row=2, column=0, sticky="w"
        )
        self.entry_autor = ctk.CTkEntry(doc, placeholder_text="Ej: Nombre del profesor")
        self.entry_autor.insert(0, doc_cfg.autor)
        self.entry_autor.grid(row=3, column=0, pady=(4, 10), sticky="ew")

        ctk.CTkLabel(doc, text="Etiqueta de las imágenes:", font=ctk.CTkFont(size=13), anchor="w").grid(
            row=4, column=0, sticky="w"
        )
        self.combo_etiqueta = ctk.CTkComboBox(
            doc, values=ETIQUETAS_DOCUMENTO, height=36
        )
        self.combo_etiqueta.set(doc_cfg.etiqueta)
        self.combo_etiqueta.grid(row=5, column=0, pady=(4, 0), sticky="ew")

        self.label_total = ctk.CTkLabel(
            card, text=f"📊 Total de ejercicios: {cfg.total}",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.label_total.grid(row=5, column=0, padx=35, pady=(24, 6), sticky="w")

        ctk.CTkButton(
            card, text="🎲 Generar PDF Aleatorio",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50, corner_radius=10, command=self._generar
        ).grid(row=6, column=0, padx=35, pady=(10, 30), sticky="ew")

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

        por_defecto = ConfiguracionDocumento()
        documento = ConfiguracionDocumento(
            titulo=self.entry_titulo.get().strip() or por_defecto.titulo,
            autor=self.entry_autor.get().strip() or por_defecto.autor,
            etiqueta=self.combo_etiqueta.get().strip() or por_defecto.etiqueta,
        )
        self.app.config_documento = documento
        self.app.generar_pdf(config, documento)


class VistaBanco(ctk.CTkFrame):
    """Vista 2: banco de ejercicios con búsqueda, filtro y galería."""

    def __init__(self, master, app: "MainWindow"):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._crear_ui()
        self.refrescar()

    def on_mostrar(self):
        self.refrescar()

    def _crear_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=25, pady=(25, 5), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="📚 Banco de Ejercicios",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header, text="Agregue, revise y elimine ejercicios con sus imágenes",
            font=ctk.CTkFont(size=13), text_color="gray"
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        ctk.CTkButton(
            header, text="➕ Agregar Ejercicio",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40, command=self.app.abrir_dialogo_agregar
        ).grid(row=0, column=1, rowspan=2, padx=10, sticky="e")

        toolbar = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        toolbar.grid(row=1, column=0, padx=25, pady=(10, 5), sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)

        self.entry_busqueda = ctk.CTkEntry(
            toolbar, placeholder_text="🔍 Buscar por nombre...", height=36
        )
        self.entry_busqueda.grid(row=0, column=0, padx=(15, 10), pady=12, sticky="ew")
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self._filtrar())

        self.combo_dificultad = ctk.CTkComboBox(
            toolbar, values=["Todas", "Básico", "Intermedio", "Difícil"],
            state="readonly", width=160, height=36
        )
        self.combo_dificultad.set("Todas")
        self.combo_dificultad.configure(command=lambda _: self._filtrar())
        self.combo_dificultad.grid(row=0, column=1, padx=(10, 15), pady=12)

        self.label_conteo = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="gray"
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
        self._filtrar()

    def _ejercicios_filtrados(self):
        todos = obtener_ejercicios()
        filtro = self.combo_dificultad.get()
        texto = self.entry_busqueda.get().strip().lower()

        if filtro != "Todas":
            todos = [e for e in todos if e.dificultad == filtro]
        if texto:
            todos = [e for e in todos if texto in e.nombre.lower()]
        return todos

    def _filtrar(self):
        ejercicios = self._ejercicios_filtrados()
        total = len(obtener_ejercicios())

        if ejercicios:
            self.galeria.actualizar(ejercicios)
            self.label_conteo.configure(text=f"Mostrando {len(ejercicios)} de {total} ejercicios")
        else:
            self.galeria.mostrar_vacio("No se encontraron ejercicios\nAjuste la búsqueda o los filtros")
            self.label_conteo.configure(text=f"{total} ejercicios en total")


class VistaEstadisticas(ctk.CTkFrame):
    """Vista 3: estadísticas del banco con métricas y gráfico."""

    def __init__(self, master, app: "MainWindow"):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._marco_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._marco_scroll.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self._marco_scroll.grid_columnconfigure(0, weight=1)

    def on_mostrar(self):
        self._renderizar()

    def _limpiar(self):
        for w in self._marco_scroll.winfo_children():
            w.destroy()

    def _renderizar(self):
        self._limpiar()

        ctk.CTkLabel(
            self._marco_scroll, text="📊 Estadísticas del Banco",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        ejercicios = obtener_ejercicios()

        if not ejercicios:
            ctk.CTkFrame(self._marco_scroll, fg_color="white", corner_radius=12).grid(
                row=1, column=0, padx=15, pady=10, sticky="nsew"
            )
            ctk.CTkLabel(
                self._marco_scroll,
                text="No hay ejercicios para mostrar estadísticas.\nAgregue ejercicios en la sección Banco.",
                font=ctk.CTkFont(size=15), text_color="gray"
            ).grid(row=1, column=0, pady=60)
            return

        stats = contar_por_dificultad()
        estad = EstadisticasBanco(
            total=len(ejercicios),
            basicos=stats.get("Básico", 0),
            intermedios=stats.get("Intermedio", 0),
            dificiles=stats.get("Difícil", 0),
        )

        cards = ctk.CTkFrame(self._marco_scroll, fg_color="transparent")
        cards.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1)

        metricas = [
            ("Total", estad.total, "#2e86de", None),
            ("Básicos", estad.basicos, COLORES_DIF["Básico"], self._estado(estad.basicos, OBJETIVOS["Básico"])),
            ("Intermedios", estad.intermedios, COLORES_DIF["Intermedio"], self._estado(estad.intermedios, OBJETIVOS["Intermedio"])),
            ("Difíciles", estad.dificiles, COLORES_DIF["Difícil"], self._estado(estad.dificiles, OBJETIVOS["Difícil"])),
        ]

        for col, (titulo, valor, color, estado) in enumerate(metricas):
            card = ctk.CTkFrame(cards, fg_color="white", corner_radius=12)
            card.grid(row=0, column=col, padx=8, sticky="nsew")

            ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=13), text_color="gray").pack(
                pady=(20, 4)
            )
            ctk.CTkLabel(card, text=str(valor), font=ctk.CTkFont(size=34, weight="bold")).pack()

            if estado:
                ctk.CTkLabel(card, text=estado, font=ctk.CTkFont(size=11), text_color=color).pack(
                    pady=(4, 18)
                )

        chart_card = ctk.CTkFrame(self._marco_scroll, fg_color="white", corner_radius=12)
        chart_card.grid(row=2, column=0, padx=15, pady=(10, 25), sticky="ew")
        chart_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            chart_card, text="Distribución por Dificultad",
            font=ctk.CTkFont(size=17, weight="bold")
        ).grid(row=0, column=0, padx=35, pady=(28, 24), sticky="w")

        self._dibujar_barras(chart_card, estad)

        ctk.CTkLabel(
            chart_card, text=f"Distribución objetivo: {OBJETIVOS['Básico']} Básicos • "
                             f"{OBJETIVOS['Intermedio']} Intermedios • {OBJETIVOS['Difícil']} Difíciles",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=2, column=0, padx=35, pady=(0, 20), sticky="w")

        if not estad.esta_completo:
            ctk.CTkLabel(
                chart_card,
                text="⚠️ El banco aún no cubre la distribución ideal.",
                font=ctk.CTkFont(size=12), text_color="#e74c3c"
            ).grid(row=3, column=0, padx=35, pady=(0, 24), sticky="w")

    def _estado(self, valor: int, minimo: int) -> str:
        return "✅ Objetivo cumplido" if valor >= minimo else "⚠️ Faltan ejercicios"

    def _dibujar_barras(self, master, estad: EstadisticasBanco):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid(row=1, column=0, padx=60, pady=(0, 20), sticky="ew")

        datos = [
            ("Básico", estad.basicos, COLORES_DIF["Básico"]),
            ("Intermedio", estad.intermedios, COLORES_DIF["Intermedio"]),
            ("Difícil", estad.dificiles, COLORES_DIF["Difícil"]),
        ]
        max_val = max(estad.basicos, estad.intermedios, estad.dificiles, 1)

        for row, (nombre, valor, color) in enumerate(datos):
            ctk.CTkLabel(
                frame, text=f"{nombre} ({valor})",
                font=ctk.CTkFont(size=13), anchor="w", width=150
            ).grid(row=row, column=0, padx=(0, 10), pady=7, sticky="w")

            barra = ctk.CTkFrame(
                frame, width=max(10, int(320 * valor / max_val)),
                height=24, fg_color=color, corner_radius=5
            )
            barra.grid(row=row, column=1, pady=7, sticky="w")
            barra.grid_propagate(False)