import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import io
import os
from typing import Callable, List, Optional, Tuple
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
            main, text="➕ Nuevo Ejercicio", font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#0c4a6e"
        ).grid(row=0, column=0, pady=(0, 20))

        ctk.CTkLabel(main, text="Nombre:", font=ctk.CTkFont(size=13), text_color="#334155", anchor="w").grid(
            row=1, column=0, sticky="ew", pady=(0, 5)
        )
        self.entry_nombre = ctk.CTkEntry(main, placeholder_text="Ej: Suma de fracciones", border_color="#bae6fd")
        self.entry_nombre.grid(row=2, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(main, text="Dificultad:", font=ctk.CTkFont(size=13), text_color="#334155", anchor="w").grid(
            row=3, column=0, sticky="ew", pady=(0, 5)
        )
        self.combo_dificultad = ctk.CTkComboBox(
            main, values=DIFICULTADES, state="readonly",
            button_color="#0284c7", button_hover_color="#0369a1"
        )
        self.combo_dificultad.set("Básico")
        self.combo_dificultad.grid(row=4, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(main, text="Imagen:", font=ctk.CTkFont(size=13), text_color="#334155", anchor="w").grid(
            row=5, column=0, sticky="ew", pady=(0, 5)
        )
        self.selector_imagen = SelectorArchivoImagen(main, on_change=lambda _: None)
        self.selector_imagen.grid(row=6, column=0, sticky="ew", pady=(0, 20))

        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=7, column=0, sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="Cancelar", height=38,
            fg_color="#64748b", hover_color="#475569", text_color="#ffffff",
            corner_radius=8, command=self.destroy
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Guardar", height=38,
            fg_color="#10b981", hover_color="#059669", text_color="#ffffff",
            corner_radius=8, command=self._guardar
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ctk.CTkButton(
            main, text="✖ Cerrar", height=36,
            fg_color="#e74c3c", hover_color="#c0392b", text_color="#ffffff",
            command=self.destroy
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
            main, text=ejercicio.nombre, font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#0c4a6e"
        ).grid(row=0, column=0, pady=(0, 12))

        diff_color = DIFICULTAD_COLORES.get(ejercicio.dificultad, "#059669")
        diff_fondo = DIFICULTAD_FONDOS.get(ejercicio.dificultad, "#d1fae5")
        ctk.CTkLabel(
            main, text=f"• {ejercicio.dificultad}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=diff_color, fg_color=diff_fondo,
            corner_radius=6, padx=16, pady=6
        ).grid(row=1, column=0, pady=(0, 20))

        datos_imagen = ejercicio.imagen
        if not datos_imagen:
            from src.core.database import obtener_ejercicio_por_id
            datos_imagen = obtener_ejercicio_por_id(ejercicio.id)

        try:
            if not datos_imagen:
                raise ValueError("Imagen no encontrada")
            img = Image.open(io.BytesIO(datos_imagen))
            max_w, max_h = 560, 400
            if img.width > max_w or img.height > max_h:
                img.thumbnail((max_w, max_h), Image.Resampling.BILINEAR)
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
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            corner_radius=8, command=self.destroy
        ).grid(row=3, column=0, pady=(20, 10))


class DialogoCargaMasiva(ctk.CTkToplevel):
    """Diálogo para cargar varias imágenes a la vez y editar nombre/dificultad de cada una."""

    def __init__(self, master, on_agregar: Callable[[List[Tuple[str, str, bytes]]], None]):
        super().__init__(master)
        self.title("Cargar Varios Ejercicios")
        self.geometry("820x640")
        self.minsize(700, 480)
        self.transient(master)
        self.grab_set()
        self.on_agregar = on_agregar
        self.filas: List[dict] = []

        self._centrar()
        self._crear_ui()

    def _centrar(self):
        self.update_idletasks()
        x = self.master.winfo_rootx() + (self.master.winfo_width() - 820) // 2
        y = self.master.winfo_rooty() + (self.master.winfo_height() - 640) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _crear_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 0), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="🖼️ Cargar Varios Ejercicios",
            font=ctk.CTkFont(size=19, weight="bold"), text_color="#0c4a6e"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header, text="Seleccione varias imágenes y ajuste nombre y dificultad de cada una",
            font=ctk.CTkFont(size=12), text_color="#64748b"
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        ctk.CTkButton(
            header, text="📂 Seleccionar imágenes", height=38,
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            corner_radius=8, command=self._seleccionar
        ).grid(row=0, column=1, rowspan=2, padx=10, sticky="e")

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="ew")
        ctk.CTkLabel(barra, text="Dificultad para todas:", text_color="#334155").pack(side="left")
        self.combo_aplicar = ctk.CTkComboBox(
            barra, values=DIFICULTADES, width=150, height=32, state="readonly",
            button_color="#0284c7", button_hover_color="#0369a1"
        )
        self.combo_aplicar.set("Básico")
        self.combo_aplicar.pack(side="left", padx=10)
        ctk.CTkButton(
            barra, text="Aplicar a todas", width=130, height=32,
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            corner_radius=8, command=self._aplicar_a_todas
        ).pack(side="left", padx=(0, 10))

        self.label_conteo = ctk.CTkLabel(
            self, text="0 imágenes cargadas", font=ctk.CTkFont(size=12), text_color="#64748b"
        )
        self.label_conteo.grid(row=2, column=0, padx=20, pady=(6, 0), sticky="w")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#eef7fc")
        self.scroll.grid(row=3, column=0, padx=20, pady=(6, 10), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.bind("<Configure>", self._fijar_scroll_region)
        self.scroll.after_idle(self._fijar_scroll_region)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, padx=20, pady=(0, 16), sticky="ew")
        footer.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            footer, text="Cancelar", height=40,
            fg_color="#64748b", hover_color="#475569", text_color="#ffffff",
            corner_radius=8, command=self.destroy
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.btn_agregar = ctk.CTkButton(
            footer, text="Agregar al banco", height=40,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#10b981", hover_color="#059669", text_color="#ffffff",
            corner_radius=8, command=self._agregar_todas
        )
        self.btn_agregar.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self.btn_agregar.configure(state="disabled")

        self._mostrar_vacio()

    def _fijar_scroll_region(self, _=None):
        """Mantiene el scrollregion del canvas de la lista de imágenes."""
        c = self.scroll._parent_canvas
        c.configure(scrollregion=(0, 0, c.winfo_width(), self.scroll.winfo_reqheight()))

    def _mostrar_vacio(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll, text="Aún no hay imágenes.\nPulse 'Seleccionar imágenes' para comenzar.",
            font=ctk.CTkFont(size=14), text_color="gray"
        ).grid(row=0, column=0, pady=60)

    def _seleccionar(self):
        archivos = filedialog.askopenfilenames(
            parent=self,
            title="Seleccionar imágenes de ejercicios",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos los archivos", "*.*")]
        )
        if not archivos:
            return

        for w in self.scroll.winfo_children():
            w.destroy()

        for ruta in archivos:
            try:
                with open(ruta, "rb") as f:
                    datos = f.read()
                img = Image.open(io.BytesIO(datos))  # valida que sea imagen
                img.thumbnail((90, 90), Image.Resampling.BILINEAR)
                prev = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            except Exception:
                messagebox.showwarning(
                    "Imagen no válida",
                    f"No se pudo cargar: {os.path.basename(ruta)}",
                    parent=self,
                )
                continue

            self._agregar_fila(datos, prev, os.path.splitext(os.path.basename(ruta))[0])

        self._actualizar_conteo()

    def _agregar_fila(self, imagen_bytes: bytes, prev, nombre_inicial: str):
        idx = len(self.filas)

        fila = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=8)
        fila.grid(row=idx, column=0, padx=4, pady=4, sticky="ew")
        fila.grid_columnconfigure(1, weight=1)

        num_label = ctk.CTkLabel(fila, text=f"{idx + 1}.", width=30, font=ctk.CTkFont(size=13, weight="bold"))
        num_label.grid(row=0, column=0, rowspan=2, padx=(10, 4))

        ctk.CTkLabel(fila, image=prev, text="").grid(
            row=0, column=1, rowspan=2, padx=(4, 12), pady=8, sticky="w"
        )

        cont = ctk.CTkFrame(fila, fg_color="transparent")
        cont.grid(row=0, column=2, padx=(0, 10), pady=(10, 4), sticky="ew")
        cont.grid_columnconfigure(0, weight=1)

        entry = ctk.CTkEntry(cont, placeholder_text="Nombre del ejercicio")
        entry.insert(0, nombre_inicial)
        entry.grid(row=0, column=0, sticky="ew")

        combo = ctk.CTkComboBox(cont, values=DIFICULTADES, width=150, height=30, state="readonly")
        combo.set("Básico")
        combo.grid(row=1, column=0, sticky="w", pady=(6, 0))

        def quitar():
            self._quitar_fila(fila)

        ctk.CTkButton(
            fila, text="✖ Quitar", width=70, height=30,
            fg_color="#e74c3c", hover_color="#c0392b", text_color="#ffffff",
            command=quitar
        ).grid(row=0, column=3, rowspan=2, padx=(0, 12))

        self.filas.append({
            "frame": fila, "entry": entry, "combo": combo,
            "imagen": imagen_bytes, "prev": prev, "num": num_label,
        })
        self.after_idle(self._fijar_scroll_region)

    def _quitar_fila(self, fila):
        for f in self.filas:
            if f["frame"] is fila:
                f["frame"].destroy()
                self.filas.remove(f)
                break
        self._renumerar()
        self._actualizar_conteo()

    def _renumerar(self):
        for i, f in enumerate(self.filas):
            f["num"].configure(text=f"{i + 1}.")

    def _actualizar_conteo(self):
        n = len(self.filas)
        self.label_conteo.configure(text=f"{n} imagen(es) cargada(s)")
        estado = "normal" if n > 0 else "disabled"
        self.btn_agregar.configure(state=estado)
        self.after_idle(self._fijar_scroll_region)

    def _aplicar_a_todas(self):
        dif = self.combo_aplicar.get()
        for f in self.filas:
            f["combo"].set(dif)

    def _agregar_todas(self):
        pendientes = []
        for i, f in enumerate(self.filas, start=1):
            nombre = f["entry"].get().strip()
            if not nombre:
                nombre = f"Ejercicio {i}"
            pendientes.append((nombre, f["combo"].get(), f["imagen"]))

        self.on_agregar(pendientes)
        self.destroy()