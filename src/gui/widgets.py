import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import io
import queue
import math
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional, List
from src.core.models import Ejercicio, DIFICULTAD_COLORES, DIFICULTAD_FONDOS
from src.core.database import obtener_miniatura


_FUENTES_CACHE: dict = {}


def _fuente_compartida(**kwargs) -> "ctk.CTkFont":
    """Reutiliza fuentes CustomTkinter (crear una por widget es muy costoso)."""
    clave = tuple(sorted(kwargs.items()))
    fuente = _FUENTES_CACHE.get(clave)
    if fuente is None:
        fuente = ctk.CTkFont(**kwargs)
        _FUENTES_CACHE[clave] = fuente
    return fuente


class EjercicioCard(ctk.CTkFrame):
    """Tarjeta que representa un ejercicio en la galería. Permite reutilización en pool."""

    def __init__(
        self,
        master,
        ejercicio: Optional[Ejercicio] = None,
        on_click: Optional[Callable[[Ejercicio], None]] = None,
        on_delete: Optional[Callable[[int], None]] = None,
        imagen_ctk: Optional[ctk.CTkImage] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.ejercicio: Optional[Ejercicio] = ejercicio
        self.on_click = on_click
        self.on_delete = on_delete

        self.configure(fg_color="#ffffff", border_width=1, border_color="#d0e6f5", corner_radius=10)
        self.grid_columnconfigure(0, weight=1)

        self._crear_ui()
        self._bind_events()

        if ejercicio is not None:
            self.actualizar_datos(ejercicio, imagen_ctk=imagen_ctk)

    def _crear_ui(self):
        self.img_label = ctk.CTkLabel(self, text="📷\nSin imagen", height=130)
        self.img_label.grid(row=0, column=0, padx=10, pady=(10, 6), sticky="ew")

        self.nombre_label = ctk.CTkLabel(
            self,
            text="",
            font=_fuente_compartida(size=13, weight="bold"),
            text_color="#0c4a6e",
            anchor="w",
            wraplength=240
        )
        self.nombre_label.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")

        self.diff_label = ctk.CTkLabel(
            self,
            text="",
            font=_fuente_compartida(size=11),
            corner_radius=4,
            padx=8,
            pady=2,
        )
        self.diff_label.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.btn_ver = ctk.CTkButton(
            btn_frame, text="Ver", height=28,
            fg_color="#0284c7", hover_color="#38bdf8", text_color="#ffffff",
            corner_radius=8,
            command=self._click_ver
        )
        self.btn_ver.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.btn_eliminar = ctk.CTkButton(
            btn_frame, text="Eliminar", height=28,
            fg_color="#f43f5e", hover_color="#e11d48", text_color="#ffffff",
            corner_radius=8,
            command=self._click_eliminar
        )
        self.btn_eliminar.grid(row=0, column=1, padx=(4, 0), sticky="ew")

    def _bind_events(self):
        for widget in [self, self.img_label]:
            widget.bind("<Button-1>", lambda e: self._click_ver())

    def _click_ver(self):
        if self.ejercicio is not None and self.on_click is not None:
            self.on_click(self.ejercicio)

    def _click_eliminar(self):
        if self.ejercicio is not None and self.on_delete is not None:
            self.on_delete(self.ejercicio.id)

    def actualizar_datos(
        self,
        ejercicio: Ejercicio,
        imagen_ctk: Optional[ctk.CTkImage] = None,
        cargando: bool = False,
    ):
        """Actualiza los datos de la tarjeta in-place sin necesidad de recrear widgets."""
        self.ejercicio = ejercicio
        self.nombre_label.configure(text=ejercicio.nombre)

        diff_color = DIFICULTAD_COLORES.get(ejercicio.dificultad, "#95a5a6")
        diff_fondo = DIFICULTAD_FONDOS.get(ejercicio.dificultad, "#ecf0f1")
        self.diff_label.configure(
            text=ejercicio.dificultad,
            text_color=diff_color,
            fg_color=diff_fondo,
        )

        if imagen_ctk is not None:
            self.set_imagen(imagen_ctk)
        elif cargando:
            self.mostrar_cargando()
        else:
            self.mostrar_sin_imagen()

    def set_imagen(self, ctk_img: ctk.CTkImage):
        self.img_label.configure(image=ctk_img, text="", height=130)

    def mostrar_cargando(self):
        self.img_label.configure(image="", text="⏳\nCargando...", height=130)

    def mostrar_sin_imagen(self):
        self.img_label.configure(image="", text="📷\nSin imagen", height=130)


class GaleriaEjercicios(ctk.CTkFrame):
    """Galería de tarjetas de alto rendimiento con paginación, carga asíncrona y pool de widgets."""

    ANCHO_MINIMO_CARD = 270

    def __init__(
        self,
        master,
        on_ejercicio_click: Callable[[Ejercicio], None],
        on_ejercicio_delete: Callable[[int], None],
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_ejercicio_click = on_ejercicio_click
        self.on_ejercicio_delete = on_ejercicio_delete

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Estado de paginación
        self.elementos_por_pagina = 12
        self.pagina_actual = 1
        self._todos_ejercicios: List[Ejercicio] = []
        self._ejercicios_pagina: List[Ejercicio] = []

        # Pool de tarjetas para reutilización total
        self._pool_cards: List[EjercicioCard] = []
        self._cards_activas: List[EjercicioCard] = []
        self._columnas_actuales = 0
        self._vacio_label: Optional[ctk.CTkLabel] = None

        # Caché de miniaturas decodificadas y generación activa
        self._thumbs_cache: dict[int, Optional[ctk.CTkImage]] = {}
        self._generacion_id = 0
        self._pool_hilos = ThreadPoolExecutor(max_workers=3, thread_name_prefix="ThumbLoader")
        self._timer_resize: Optional[str] = None

        # Contenedor con scroll para las tarjetas
        self.scroll_cards = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_cards.grid(row=0, column=0, sticky="nsew")

        # Barra inferior de paginación Frutiger Aero
        self.pagination_frame = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12, border_width=1, border_color="#d0e6f5", height=48)
        self.pagination_frame.grid(row=1, column=0, pady=(10, 0), sticky="ew")
        self._crear_barra_paginacion()

        # Manejador debounced para redimensionado suave de ventana
        self.scroll_cards.bind("<Configure>", self._on_configure_debounced)

    def _crear_barra_paginacion(self):
        self.pagination_frame.grid_columnconfigure(2, weight=1)

        self.btn_primera = ctk.CTkButton(
            self.pagination_frame, text="⏮", width=36, height=32,
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            corner_radius=8,
            command=self._ir_primera_pagina
        )
        self.btn_primera.grid(row=0, column=0, padx=(12, 4), pady=8)

        self.btn_anterior = ctk.CTkButton(
            self.pagination_frame, text="◀ Anterior", width=95, height=32,
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            corner_radius=8,
            command=self._ir_anterior_pagina
        )
        self.btn_anterior.grid(row=0, column=1, padx=4, pady=8)

        self.lbl_info_pagina = ctk.CTkLabel(
            self.pagination_frame,
            text="Página 1 de 1 (0 ejercicios)",
            font=_fuente_compartida(size=13, weight="bold"),
            text_color="#0c4a6e"
        )
        self.lbl_info_pagina.grid(row=0, column=2, padx=12, pady=8)

        self.btn_siguiente = ctk.CTkButton(
            self.pagination_frame, text="Siguiente ▶", width=95, height=32,
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            corner_radius=8,
            command=self._ir_siguiente_pagina
        )
        self.btn_siguiente.grid(row=0, column=3, padx=4, pady=8)

        self.btn_ultima = ctk.CTkButton(
            self.pagination_frame, text="⏭", width=36, height=32,
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            corner_radius=8,
            command=self._ir_ultima_pagina
        )
        self.btn_ultima.grid(row=0, column=4, padx=(4, 8), pady=8)

        self.combo_tamano = ctk.CTkComboBox(
            self.pagination_frame,
            values=["12 por pág.", "24 por pág.", "36 por pág."],
            width=115, height=32,
            state="readonly",
            button_color="#0284c7", button_hover_color="#0369a1",
            command=self._on_cambio_tamano_pagina
        )
        self.combo_tamano.set("12 por pág.")
        self.combo_tamano.grid(row=0, column=5, padx=(8, 12), pady=8)

    def _total_paginas(self) -> int:
        n = len(self._todos_ejercicios)
        return max(1, math.ceil(n / self.elementos_por_pagina))

    def _ir_primera_pagina(self):
        if self.pagina_actual > 1:
            self.pagina_actual = 1
            self._renderizar_pagina()

    def _ir_anterior_pagina(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self._renderizar_pagina()

    def _ir_siguiente_pagina(self):
        if self.pagina_actual < self._total_paginas():
            self.pagina_actual += 1
            self._renderizar_pagina()

    def _ir_ultima_pagina(self):
        total = self._total_paginas()
        if self.pagina_actual < total:
            self.pagina_actual = total
            self._renderizar_pagina()

    def _on_cambio_tamano_pagina(self, seleccion: str):
        try:
            num = int(seleccion.split()[0])
            if num != self.elementos_por_pagina:
                self.elementos_por_pagina = num
                self.pagina_actual = 1
                self._renderizar_pagina()
        except Exception:
            pass

    def _on_configure_debounced(self, event=None):
        if self._timer_resize is not None:
            try:
                self.after_cancel(self._timer_resize)
            except Exception:
                pass
        self._timer_resize = self.after(65, self._reorganizar_grid)

    def limpiar_cache(self):
        """Invalida la caché de miniaturas."""
        self._thumbs_cache.clear()

    def actualizar(self, ejercicios: List[Ejercicio], reiniciar: bool = False):
        """Actualiza la lista de ejercicios a mostrar y renderiza la página correspondiente."""
        self._eliminar_vacio()
        self._todos_ejercicios = list(ejercicios)

        if reiniciar:
            self.pagina_actual = 1
        else:
            total_pags = self._total_paginas()
            if self.pagina_actual > total_pags:
                self.pagina_actual = total_pags

        self.pagination_frame.grid()
        self._renderizar_pagina()

    def mostrar_vacio(self, mensaje: str):
        """Muestra mensaje de galería vacía ocultando tarjetas y barra de paginación."""
        self._eliminar_vacio()
        self._todos_ejercicios = []
        self._generacion_id += 1

        for card in self._pool_cards:
            card.grid_remove()
        self._cards_activas.clear()
        self.pagination_frame.grid_remove()

        self._vacio_label = ctk.CTkLabel(
            self.scroll_cards, text=mensaje, font=_fuente_compartida(size=15), text_color="gray"
        )
        self._vacio_label.grid(row=0, column=0, pady=70, sticky="nsew")
        self.scroll_cards.grid_columnconfigure(0, weight=1)

    def _eliminar_vacio(self):
        if self._vacio_label is not None:
            try:
                self._vacio_label.destroy()
            except Exception:
                pass
            self._vacio_label = None

    def _renderizar_pagina(self):
        """Renderiza la porción de tarjetas correspondiente a la página activa reutilizando el pool."""
        self._eliminar_vacio()
        self._generacion_id += 1
        gen_actual = self._generacion_id

        total_ejercicios = len(self._todos_ejercicios)
        total_pags = self._total_paginas()
        if self.pagina_actual > total_pags:
            self.pagina_actual = total_pags
        if self.pagina_actual < 1:
            self.pagina_actual = 1

        # Actualizar controles de paginación
        self.lbl_info_pagina.configure(
            text=f"Página {self.pagina_actual} de {total_pags}  ({total_ejercicios} ejercicios)"
        )
        self.btn_primera.configure(state="normal" if self.pagina_actual > 1 else "disabled")
        self.btn_anterior.configure(state="normal" if self.pagina_actual > 1 else "disabled")
        self.btn_siguiente.configure(state="normal" if self.pagina_actual < total_pags else "disabled")
        self.btn_ultima.configure(state="normal" if self.pagina_actual < total_pags else "disabled")

        # Obtener recorte de la página
        idx_ini = (self.pagina_actual - 1) * self.elementos_por_pagina
        idx_fin = idx_ini + self.elementos_por_pagina
        ejercicios_pagina = self._todos_ejercicios[idx_ini:idx_fin]
        self._ejercicios_pagina = ejercicios_pagina

        # Asegurar que el pool de tarjetas tenga al menos la cantidad requerida
        cant_necesaria = len(ejercicios_pagina)
        while len(self._pool_cards) < cant_necesaria:
            card = EjercicioCard(
                self.scroll_cards,
                on_click=self.on_ejercicio_click,
                on_delete=self.on_ejercicio_delete,
            )
            self._pool_cards.append(card)

        # Configurar tarjetas activas y ocultar las sobrantes del pool
        self._cards_activas = self._pool_cards[:cant_necesaria]
        for card in self._pool_cards[cant_necesaria:]:
            card.grid_remove()

        # Asignar datos y solicitar miniaturas
        for card, ej in zip(self._cards_activas, ejercicios_pagina):
            cached = self._thumbs_cache.get(ej.id)
            if cached is not None:
                card.actualizar_datos(ej, imagen_ctk=cached)
            else:
                card.actualizar_datos(ej, cargando=True)
                self._encolar_miniatura(ej.id, gen_actual)

        # Ubicar en grid y resetear scroll vertical
        self._reorganizar_grid()
        try:
            self.scroll_cards._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _reorganizar_grid(self):
        """Ubica las tarjetas activas en columnas adaptables sin recalcular geometría innecesariamente."""
        self._timer_resize = None
        ancho = self.scroll_cards.winfo_width()
        columnas = max(1, int(ancho // self.ANCHO_MINIMO_CARD)) if ancho > 100 else 3

        if columnas != self._columnas_actuales:
            self._columnas_actuales = columnas
            for i in range(columnas):
                self.scroll_cards.grid_columnconfigure(i, weight=1)
            for i in range(columnas, 8):
                self.scroll_cards.grid_columnconfigure(i, weight=0)

        for idx, card in enumerate(self._cards_activas):
            fila, col = divmod(idx, columnas)
            card.grid(row=fila, column=col, padx=8, pady=8, sticky="nsew")

    def _encolar_miniatura(self, ejercicio_id: int, gen_id: int):
        """Carga y decodifica la miniatura en un hilo secundario para evitar cualquier bloqueo."""
        def tarea():
            try:
                mini_bytes = obtener_miniatura(ejercicio_id)
                if not mini_bytes:
                    return ejercicio_id, None, gen_id
                img = Image.open(io.BytesIO(mini_bytes))
                img.thumbnail((260, 180), Image.Resampling.BILINEAR)
                return ejercicio_id, img, gen_id
            except Exception:
                return ejercicio_id, None, gen_id

        def al_terminar(fut):
            try:
                eid, pil_img, gid = fut.result()
                if gid == self._generacion_id:
                    self.after(0, lambda: self._aplicar_miniatura_cargada(eid, pil_img, gid))
            except Exception:
                pass

        fut = self._pool_hilos.submit(tarea)
        fut.add_done_callback(al_terminar)

    def _aplicar_miniatura_cargada(self, eid: int, pil_img: Optional[Image.Image], gid: int):
        if gid != self._generacion_id:
            return

        ctk_img = None
        if pil_img is not None:
            try:
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                self._thumbs_cache[eid] = ctk_img
            except Exception:
                ctk_img = None

        # Si alguna tarjeta visible corresponde a este ejercicio, actualizarla
        for card in self._cards_activas:
            if card.ejercicio is not None and card.ejercicio.id == eid:
                if ctk_img is not None:
                    card.set_imagen(ctk_img)
                else:
                    card.mostrar_sin_imagen()
                break


class SelectorArchivoImagen(ctk.CTkFrame):
    """Selector de archivo de imagen con vista previa rápida."""

    def __init__(self, master, on_change: Callable[[bytes], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_change = on_change
        self.imagen_bytes: Optional[bytes] = None

        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Ninguna imagen seleccionada", text_color="gray")
        self.label.grid(row=0, column=0, padx=10, pady=(10, 8), sticky="ew")

        ctk.CTkButton(
            self, text="Seleccionar imagen", height=34,
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            corner_radius=8, command=self._seleccionar
        ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        self.preview = ctk.CTkLabel(self, text="")
        self.preview.grid(row=2, column=0, padx=10, pady=(0, 10))

    def _seleccionar(self):
        path = filedialog.askopenfilename(
            title="Seleccionar imagen del ejercicio",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "rb") as f:
                self.imagen_bytes = f.read()

            img = Image.open(io.BytesIO(self.imagen_bytes))
            img.thumbnail((200, 200), Image.Resampling.BILINEAR)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.preview.configure(image=ctk_img, text="")
            self.label.configure(text=path.split("/")[-1].split("\\")[-1], text_color="black")
            self.on_change(self.imagen_bytes)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen: {e}")

    def obtener_imagen(self) -> Optional[bytes]:
        return self.imagen_bytes

    def limpiar(self):
        self.imagen_bytes = None
        self.label.configure(text="Ninguna imagen seleccionada", text_color="gray")
        self.preview.configure(image="", text="")


class SpinboxNumerico(ctk.CTkFrame):
    """Campo numérico con botones de incremento/decremento."""

    def __init__(self, master, texto: str, min_val: int = 0, max_val: int = 60, default: int = 0, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.min_val = min_val
        self.max_val = max_val
        self.valor = default

        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=texto, font=_fuente_compartida(size=13), text_color="#334155").grid(
            row=0, column=0, padx=(25, 15)
        )

        self.entry = ctk.CTkEntry(self, width=70, justify="center", border_color="#bae6fd")
        self.entry.insert(0, str(default))
        self.entry.grid(row=0, column=1, sticky="w")
        self.entry.bind("<FocusOut>", self._validar)
        self.entry.bind("<Return>", self._validar)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=(5, 10))
        ctk.CTkButton(
            btn_frame, text="▲", width=30, height=26,
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            command=self._incrementar
        ).pack(pady=(0, 2))
        ctk.CTkButton(
            btn_frame, text="▼", width=30, height=26,
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            command=self._decrementar
        ).pack()

    def _validar(self, event=None):
        try:
            val = int(self.entry.get())
        except ValueError:
            val = self.valor
        self.valor = max(self.min_val, min(self.max_val, val))
        self.entry.delete(0, "end")
        self.entry.insert(0, str(self.valor))

    def _incrementar(self):
        if self.valor < self.max_val:
            self.valor += 1
            self.actualizar_entry()

    def _decrementar(self):
        if self.valor > self.min_val:
            self.valor -= 1
            self.actualizar_entry()

    def actualizar_entry(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(self.valor))

    def obtener(self) -> int:
        self._validar()
        return self.valor


class DialogoProgreso(ctk.CTkToplevel):
    """Diálogo modal con barra de progreso seguro para hilos."""

    def __init__(self, master, titulo: str = "Procesando...", ancho: int = 380, alto: int = 140):
        super().__init__(master)
        self.title(titulo)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Iniciando...", font=_fuente_compartida(size=13))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 12))

        self.progress = ctk.CTkProgressBar(self, width=ancho - 60, progress_color="#10b981")
        self.progress.grid(row=1, column=0, padx=20, pady=(0, 5))
        self.progress.set(0)

        self._cola: "queue.Queue[tuple]" = queue.Queue()
        self._centrar(ancho, alto)
        self._poll()

    def _centrar(self, ancho: int, alto: int):
        self.update_idletasks()
        x = self.master.winfo_rootx() + (self.master.winfo_width() - ancho) // 2
        y = self.master.winfo_rooty() + (self.master.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{max(x, 0)}+{max(y, 0)}")

    def _poll(self):
        try:
            while True:
                item = self._cola.get_nowait()
                self._despachar(item)
        except queue.Empty:
            pass
        except Exception:
            pass
        try:
            self.after(50, self._poll)
        except Exception:
            pass

    def _despachar(self, item: tuple):
        tipo = item[0]
        if tipo == "progreso":
            self.actualizar(item[1], item[2])
        elif tipo == "exito":
            self.finalizar_exitoso(item[1])
        elif tipo == "error":
            self.finalizar_error(item[1])

    def actualizar(self, mensaje: str, progreso: float):
        self.label.configure(text=mensaje)
        self.progress.set(progreso)
        self.update_idletasks()

    def actualizar_seguro(self, mensaje: str, progreso: float):
        """Actualización invocable desde un hilo distinto al principal."""
        self._cola.put(("progreso", mensaje, progreso))

    def finalizar_seguro(self, tipo: str, dato):
        """Finalización (exito/error) invocable desde un hilo distinto al principal."""
        self._cola.put((tipo, dato))

    def finalizar_exitoso(self, dato):
        pass

    def finalizar_error(self, error: str):
        pass

    def finalizar(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class DialogoProgresoPDF(DialogoProgreso):
    """Diálogo de progreso para la generación de PDF."""

    def __init__(self, master):
        super().__init__(master, "Generando PDF...")
        self.resultado: Optional[str] = None
        self.error: Optional[str] = None

    def finalizar_exitoso(self, archivo: str):
        self.resultado = archivo
        self.actualizar("✅ PDF generado correctamente", 1.0)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, pady=(15, 20))
        ctk.CTkButton(
            frame, text="📂 Abrir PDF", width=130, height=34,
            fg_color="#10b981", hover_color="#059669", text_color="#ffffff",
            corner_radius=8,
            command=lambda: abrir_archivo(archivo)
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            frame, text="Cerrar", width=100, height=34,
            fg_color="#64748b", hover_color="#475569", text_color="#ffffff",
            corner_radius=8, command=self.finalizar
        ).pack(side="left", padx=6)

    def finalizar_error(self, error: str):
        self.error = error
        self.actualizar(f"❌ {error}", 0)
        self.label.configure(text_color="#e74c3c")
        ctk.CTkButton(
            self, text="Cerrar", width=100,
            fg_color="#e74c3c", hover_color="#c0392b", text_color="#ffffff",
            command=self.finalizar
        ).grid(row=2, column=0, pady=(15, 20))


def abrir_archivo(path: str):
    """Abre un archivo con la aplicación por defecto del sistema."""
    import os
    import sys
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", path])
        else:
            import subprocess
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass
