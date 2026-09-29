# Generador de Ejercicios PDF

Aplicación de escritorio para Windows que gestiona un banco de **prácticas académicas** (matemáticas, letras, etc.) con imágenes y genera documentos PDF (exámenes/galerías) con prácticas **seleccionadas aleatoriamente** por nivel de dificultad.

## ▶️ Cómo empezar (usuario final)

1. **Copie la carpeta `dist/`** a la PC donde quiera usarla (escritorio, USB, red, etc.).
2. **Doble clic en `GeneradorEjercicios.exe`** — se abre la ventana principal.
3. **No necesita Python ni instalar nada.** Todo está incluido en el ejecutable.

> ⚠️ **Primer arranque:** el ejecutable tarda unos segundos en iniciar (descomprime sus archivos internos). Es normal.
>
> ⚠️ **Antivirus / SmartScreen:** al no estar firmado, Windows o el antivirus pueden mostrar una advertencia la primera vez → "Más información" → "Ejecutar de todas formas".

La base de datos `ejercicios.db` (los ejercicios del banco) se guarda **junto al .exe** y se crea automáticamente si no existe.

## 🖥️ Pantalla principal

La ventana tiene un **panel lateral** con 3 secciones:

| Sección | Para qué sirve |
|---------|----------------|
| 🎲 **Generar PDF** | Crear un documento con ejercicios aleatorios |
| 📚 **Banco de Ejercicios** | Ver, buscar, agregar y eliminar ejercicios |
| 📊 **Estadísticas** | Cantidad de ejercicios por dificultad y estado del banco |

---

## 🎲 Sección 1 — Generar PDF

1. Escriba cuántos ejercicios quiere de cada nivel: **Básicos, Intermedios, Difíciles** (botones ▲/▼ o escriba el número).
2. **Opcional — Personalizar Documento:**
   - **Título**: escriba el título del documento (ej: "Examen Parcial de Matemáticas").
   - **Autor**: nombre que aparecerá en el encabezado.
   - **Etiqueta**: elija o escriba la palabra que acompaña a cada imagen (Ejercicio, Enunciado, Problema, Pregunta, Actividad, etc.).
3. Verifique el total en *"📊 Total de ejercicios"*.
4. Pulse **"🎲 Generar PDF Aleatorio"**.
5. Elija **carpeta y nombre** del archivo y pulse *Guardar*.
6. Al terminar verá *"✅ PDF generado correctamente"* → puede pulsar **"📂 Abrir PDF"** para verlo o cerrar.

**Notas:**
- Si los campos de título o autor quedan vacíos se usan los valores por defecto.
- Si el banco no tiene suficientes ejercicios de un nivel, el programa avisa y pregunta si desea continuar con los disponibles.
- El documento generado usa 2 columnas con la imagen de cada ejercicio numerada (con la etiqueta elegida).

## 📚 Sección 2 — Banco de Ejercicios

- **➕ Agregar Ejercicio** (botón superior derecho):
  1. Escriba el **nombre** del ejercicio.
  2. Elija la **dificultad** (Básico / Intermedio / Difícil).
  3. Pulse **"Seleccionar imagen"** y elija un archivo `.png`, `.jpg` o `.jpeg`.
  4. Pulse **Guardar**.

- **Galeria:** los ejercicios se muestran como tarjetas con miniatura, nombre y dificultad.
  - **🔍 Buscar** por nombre (campo superior) y **filtrar** por dificultad (menú desplegable).
  - **Ver:** haga clic en una tarjeta → se abre la imagen ampliada.
  - **Eliminar:** haga clic en **Eliminar** en la tarjeta → confirme.

## 📊 Sección 3 — Estadísticas

- Muestra el **total** de ejercicios y el conteo por nivel.
- Indica si cada nivel cumple la **distribución objetivo** (30 Básicos / 20 Intermedios / 10 Difíciles).
- Barra de distribución actual de todo el banco.

---

## 🔁 Mantener / actualizar la aplicación

- **Guardar sus ejercicios al actualizar el .exe:** el programa nuevo se copia sobre el antiguo, pero **no borre `ejercicios.db`** — ahí viven sus ejercicios.
- **Reiniciar desde cero:** elimine `ejercicios.db` y la próxima vez que abra la app se crea un banco vacío.

## 🗄️ Archivos del proyecto

```
pruebaproyecto/
├── dist/                          ← APLICACIÓN PARA EL USUARIO
│   ├── GeneradorEjercicios.exe    ← ejecutable (no requiere Python)
│   └── ejercicios.db              ← banco de ejercicios (se crea sola)
├── src/
│   ├── main.py                    ← punto de entrada (modo desarrollo)
│   ├── core/                      ← lógica: base de datos, PDF, modelos
│   └── gui/                       ← interfaz: ventana, vistas, diálogos
├── app.py                         ← versión original (Streamlit, obsoleta)
├── GeneradorEjercicios.spec       ← especificación de PyInstaller
├── app.ico                        ← icono del ejecutable
└── README.md
```

## 🛠️ Para desarrolladores

**Ejecutar desde el código fuente:**

```bash
pip install customtkinter fpdf2 pillow
python src/main.py
```

**Recompilar el ejecutable:**

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name GeneradorEjercicios --icon app.ico src/main.py
```

El .exe resultante queda en `dist/`. Si quiere distribuir con el banco ya poblado, copie también `ejercicios.db` a `dist/`.

---

Proyecto desarrollado por **Angel Fabiano Salas Zapata**. Conversión a aplicación de escritorio con CustomTkinter y empaquetado con PyInstaller.