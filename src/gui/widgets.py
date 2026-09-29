import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import io
import queue
from typing import Callable, Optional
from src.core.models import Ejercicio, DIFICULTAD_COLORES, DIFICULTAD_FONDOS


class EjercicioCard(ctk.CTkFrame):
    """Tarjeta que representa un ejercicio en la galería."""

    def __init__(
        self,
        master,
        ejercicio: Ejercicio,
        on_click: Callable[[Ejercicio], None],
        on_delete: Callable[[int], None],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.ejercicio = ejercicio
        self.on_click = on_click
        self.on_delete = on_delete

        self.configure(fg_color="white", border_width=1, border_color="#ddd", corner_radius=8)
        self.grid_columnconfigure(0, weight=1)

        self._crear_ui()
        self._bind_events()

    def _crear_ui(self):
        try:
            img = Image.open(io.BytesIO(self.ejercicio.imagen))
            img.thumbnail((260, 180), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.img_label = ctk.CTkLabel(self, image=ctk_img, text="")
        except Exception:
            self.img_label = ctk.CTkLabel(self, text="📷\nSin imagen", height=120)
        self.img_label.grid(row=0, column=0, padx=10, pady=(12, 8), sticky="ew")

        ctk.CTkLabel(
            self,
            text=self.ejercicio.nombre,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            wraplength=240
        ).grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")

        diff_color = DIFICULTAD_COLORES.get(self.ejercicio.dificultad, "#95a5a6")
        diff_fondo = DIFICULTAD_FONDOS.get(self.ejercicio.dificultad, "#ecf0f1")
        ctk.CTkLabel(
            self,
            text=self.ejercicio.dificultad,
            font=ctk.CTkFont(size=11),
            text_color=diff_color,
            fg_color=diff_fondo,
            corner_radius=4
        ).grid(row=2, column=0, padx=12, pady=(0, 8), sticky="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="Ver", height=28,
            command=lambda: self.on_click(self.ejercicio)
        ).grid(row=0, column=0, padx=(0, 4), sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Eliminar", height=28,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=lambda: self.on_delete(self.ejercicio.id)
        ).grid(row=0, column=1, padx=(4, 0), sticky="ew")

    def _bind_events(self):
        for widget in [self, self.img_label]:
            widget.bind("<Button-1>", lambda e: self.on_click(self.ejercicio))


class GaleriaEjercicios(ctk.CTkScrollableFrame):
    """Galería tipo grid de tarjetas con número de columnas adaptativo."""

    ANCHO_MINIMO_CARD = 280

    def __init__(
        self,
        master,
        on_ejercicio_click: Callable[[Ejercicio], None],
        on_ejercicio_delete: Callable[[int], None],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_ejercicio_click = on_ejercicio_click
        self.on_ejercicio_delete = on_ejercicio_delete

        self._ejercicios: list[Ejercicio] = []
        self._cards: list[EjercicioCard] = []
        self._columnas_actuales = 0
        self._vacio_label: Optional[ctk.CTkLabel] = None

        self.bind("<Configure>", lambda e: self._reorganizar())

    def actualizar(self, ejercicios: list[Ejercicio]):
        self._eliminar_vacio()
        self._ejercicios = list(ejercicios)
        self._columnas_actuales = 0
        self._reorganizar()

    def mostrar_vacio(self, mensaje: str):
        self._eliminar_vacio()
        self._ejercicios = []
        self._destruir_cards()
        self._columnas_actuales = 0
        self._vacio_label = ctk.CTkLabel(
            self, text=mensaje, font=ctk.CTkFont(size=15), text_color="gray"
        )
        self._vacio_label.pack(pady=60)

    def _reorganizar(self):
        self._eliminar_vacio()
        ancho = self.winfo_width()
        columnas = max(1, int(ancho // self.ANCHO_MINIMO_CARD)) if ancho > 100 else 3

        if columnas == self._columnas_actuales and self._cards:
            return

        self._destruir_cards()
        self._columnas_actuales = columnas

        for i in range(columnas):
            self.grid_columnconfigure(i, weight=1)

        for idx, ej in enumerate(self._ejercicios):
            fila, col = divmod(idx, columnas)
            card = EjercicioCard(
                self,
                ejercicio=ej,
                on_click=self.on_ejercicio_click,
                on_delete=self.on_ejercicio_delete,
            )
            card.grid(row=fila, column=col, padx=8, pady=8, sticky="nsew")
            self._cards.append(card)

    def _destruir_cards(self):
        for card in self._cards:
            card.destroy()
        self._cards.clear()

    def _eliminar_vacio(self):
        if self._vacio_label is not None:
            self._vacio_label.destroy()
            self._vacio_label = None


class SelectorArchivoImagen(ctk.CTkFrame):
    """Selector de archivo de imagen con vista previa."""

    def __init__(self, master, on_change: Callable[[bytes], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_change = on_change
        self.imagen_bytes: Optional[bytes] = None

        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Ninguna imagen seleccionada", text_color="gray")
        self.label.grid(row=0, column=0, padx=10, pady=(10, 8), sticky="ew")

        ctk.CTkButton(
            self, text="Seleccionar imagen", height=34, command=self._seleccionar
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
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.preview.configure(image=ctk_img, text="")
            self.label.configure(text=path.split("/")[-1], text_color="black")
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

        ctk.CTkLabel(self, text=texto, font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(25, 15)
        )

        self.entry = ctk.CTkEntry(self, width=70, justify="center")
        self.entry.insert(0, str(default))
        self.entry.grid(row=0, column=1, sticky="w")
        self.entry.bind("<FocusOut>", self._validar)
        self.entry.bind("<Return>", self._validar)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=(5, 10))
        ctk.CTkButton(btn_frame, text="▲", width=30, height=26, command=self._incrementar).pack()
        ctk.CTkButton(btn_frame, text="▼", width=30, height=26, command=self._decrementar).pack()

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
    """Diálogo modal con barra de progreso.

    Comunicación hilo->GUI segura mediante cola: el hilo trabajador solo
    hace put() en la cola y un poller en el hilo principal procesa los
    mensajes con self.after().
    """

    def __init__(self, master, titulo: str = "Procesando...", ancho: int = 380, alto: int = 140):
        super().__init__(master)
        self.title(titulo)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Iniciando...", font=ctk.CTkFont(size=13))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 12))

        self.progress = ctk.CTkProgressBar(self, width=ancho - 60)
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
            command=lambda: abrir_archivo(archivo)
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            frame, text="Cerrar", width=100, height=34,
            fg_color="gray", hover_color="#555", command=self.finalizar
        ).pack(side="left", padx=6)

    def finalizar_error(self, error: str):
        self.error = error
        self.actualizar(f"❌ {error}", 0)
        self.label.configure(text_color="#e74c3c")
        ctk.CTkButton(
            self, text="Cerrar", width=100,
            fg_color="#e74c3c", hover_color="#c0392b", command=self.finalizar
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