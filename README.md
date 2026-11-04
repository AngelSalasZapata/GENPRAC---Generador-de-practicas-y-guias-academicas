# Generador de Ejercicios PDF

Aplicación de escritorio para Windows que gestiona un banco de **prácticas académicas** (matemáticas, letras, etc.) con imágenes y genera documentos PDF (exámenes/guías) con prácticas **seleccionadas aleatoriamente** por nivel de dificultad.

> La versión principal es **Avalonia** (C#/.NET 8). La versión Python/CustomTkinter se conserva como referencia de mantenimiento.

---

## ▶️ Cómo empezar (usuario final)

1. **Copie la carpeta `dist-avalonia/`** a la PC donde quiera usarla (escritorio, USB, red, etc.).
2. **Doble clic en `GeneradorEjerciciosAvalonia.exe`** — se abre la ventana principal.
3. **No necesita instalar nada.** El ejecutable es autocontenido (.NET self-contained).

> ⚠️ **Antivirus / SmartScreen:** al no estar firmado, Windows puede mostrar una advertencia la primera vez → "Más información" → "Ejecutar de todas formas".

La base de datos `ejercicios.db` se guarda **junto al `.exe`** y se crea automáticamente al primer arranque.

---

## 🖥️ Pantalla principal

La ventana tiene un **panel lateral** con 2 secciones:

| Sección | Para qué sirve |
|---------|----------------|
| 🎲 **Generar PDF** | Crear un documento con ejercicios aleatorios por nivel |
| 📚 **Banco de Ejercicios** | Ver, buscar, agregar y eliminar ejercicios |

---

## 🎲 Sección 1 — Generar PDF

1. Escriba cuántos ejercicios quiere de cada nivel: **Básicos, Intermedios, Difíciles**.
2. **Opcional — Personalizar Documento:**
   - **Título**: título del documento (ej: "Examen Parcial de Matemáticas").
   - **Autor**: nombre que aparecerá en el encabezado.
   - **Etiqueta**: palabra que acompaña cada imagen (Ejercicio, Enunciado, Problema, etc.).
   - **Espacio extra (cm)**: margen adicional bajo cada ejercicio para que el estudiante responda.
3. Verifique el total en *"📊 Total de ejercicios"*.
4. Pulse **"🎲 Generar PDF Aleatorio"**.
5. Elija carpeta y nombre del archivo → pulse *Guardar*.
6. Al terminar, pulse **"📂 Abrir PDF"** o cierre el aviso.

**Notas:**
- Si el banco no tiene suficientes ejercicios de un nivel, el programa avisa y pregunta si continuar con los disponibles.
- El documento usa 2 columnas con la imagen de cada ejercicio numerada.

---

## 📚 Sección 2 — Banco de Ejercicios

- **➕ Agregar Ejercicio** — escribe nombre, elige dificultad y selecciona imagen (`.png`, `.jpg`, `.jpeg`).
- **🖼️ Cargar Varios** — carga masiva: selecciona varias imágenes a la vez.
- **Galería paginada** (24 tarjetas por página): miniaturas precalculadas para máxima fluidez.
  - **🔍 Buscar** por nombre y **filtrar** por dificultad (menú desplegable).
  - **◀ / ▶** controles de página inferiores.
  - **Ver** — clic en una tarjeta → imagen ampliada.
  - **Eliminar** — botón en la tarjeta → confirmación.

---

## 🔁 Mantener / actualizar la aplicación

- **Al actualizar el `.exe`:** copie el nuevo ejecutable sobre el antiguo **sin borrar `ejercicios.db`**.
- **Reiniciar desde cero:** elimine `ejercicios.db`; la próxima ejecución crea un banco vacío.

---

## 🗄️ Estructura del proyecto

```
GENPRAC/
├── dist-avalonia/                     ← ✅ DISTRIBUCIÓN PRINCIPAL (usuario final)
│   ├── GeneradorEjerciciosAvalonia.exe  ← ejecutable self-contained
│   └── ejercicios.db                  ← banco de ejercicios
│
├── GeneradorEjerciciosAvalonia/       ← código fuente Avalonia (C# / .NET 8) — versión activa
│   ├── Models/                        ← entidades y constantes
│   ├── Services/                      ← base de datos, PDF (QuestPDF), helpers de imagen
│   ├── ViewModels/                    ← lógica MVVM
│   └── Views/                         ← AXAML: ventanas y controles
│
├── src/                               ← código fuente Python (CustomTkinter) — mantenimiento
│   ├── main.py                        ← punto de entrada Python
│   ├── core/                          ← modelos, base de datos, generador PDF (fpdf2)
│   └── gui/                           ← widgets, vistas, diálogos
│
├── dist/                              ← distribución Python (referencia, no activa)
│   └── GeneradorEjercicios.exe
│
├── app.py                             ← prototipo original Streamlit (archivado)
├── ejercicios.db                      ← DB de desarrollo Python (raíz del proyecto)
├── app.ico                            ← icono de la aplicación
└── README.md
```

> **Nota sobre la base de datos:** Python usa `ejercicios.db` en la raíz del proyecto; Avalonia usa `ejercicios.db` junto a su ejecutable. Para migrar ejercicios de Python a Avalonia copie el archivo:
> ```
> copy ejercicios.db dist-avalonia\ejercicios.db
> ```

---

## 🛠️ Para desarrolladores

### Versión Avalonia (principal)

```bash
# Requisitos: .NET 8 SDK
cd GeneradorEjerciciosAvalonia
dotnet run
```

**Recompilar distribución self-contained:**

```bash
dotnet publish GeneradorEjerciciosAvalonia/GeneradorEjerciciosAvalonia.csproj ^
  -c Release -r win-x64 --self-contained true ^
  -p:PublishSingleFile=true -o dist-avalonia
```

### Versión Python (mantenimiento)

```bash
pip install customtkinter fpdf2 pillow
python src/main.py
```

---

## 📊 Comparación de versiones

| Característica | Python (`src/`) | Avalonia (principal) |
|---|---|---|
| Generación PDF | ✅ fpdf2 + BytesIO | ✅ QuestPDF |
| Carga masiva | ✅ | ✅ |
| Miniatura en DB | ✅ columna `miniatura` BLOB | ✅ columna `miniatura` BLOB |
| Paginación galería | ✅ 12/24/36 por página | ✅ 24 por página |
| Carga async de thumbs | ✅ ThreadPoolExecutor | ✅ Task.Run + SemaphoreSlim |
| Buscar + filtrar | ✅ debounced 220 ms | ✅ reactivo (MVVM) |
| WAL mode + índices | ✅ | ✅ |
| Paleta Frutiger Aero | ✅ | ✅ |
| Distribución | PyInstaller (.exe) | .NET self-contained (.exe) |
| Inicio en frío | ~3-5 s (descompresión) | < 1 s |

---

Proyecto desarrollado por **Angel Fabiano Salas Zapata**.
