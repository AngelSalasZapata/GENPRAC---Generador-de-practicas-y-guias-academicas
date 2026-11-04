using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Platform.Storage;
using GeneradorEjerciciosAvalonia.Models;
using GeneradorEjerciciosAvalonia.Services;

namespace GeneradorEjerciciosAvalonia.Views;

public partial class AgregarEjercicioWindow : Window
{
    private byte[]? _imagen;

    public (string Nombre, string Dificultad, byte[] Imagen)? Resultado { get; private set; }

    public AgregarEjercicioWindow()
    {
        InitializeComponent();
        ComboDificultad.ItemsSource = Constantes.Dificultades;
        ComboDificultad.SelectedIndex = 0;
    }

    public static async Task<(string Nombre, string Dificultad, byte[] Imagen)?> ShowAsync(Window owner)
    {
        var ventana = new AgregarEjercicioWindow();
        var aceptado = await ventana.ShowDialog<bool>(owner);
        return aceptado ? ventana.Resultado : null;
    }

    private async void Seleccionar_Click(object? sender, RoutedEventArgs e)
    {
        var archivos = await StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
        {
            Title = "Seleccionar imagen del ejercicio",
            AllowMultiple = false,
            FileTypeFilter = new[]
            {
                new FilePickerFileType("Imágenes") { Patterns = new[] { "*.png", "*.jpg", "*.jpeg" } },
                FilePickerFileTypes.All,
            },
        });

        if (archivos.Count == 0) return;

        var bytes = await StorageHelpers.LeerBytesAsync(archivos[0]);
        var miniatura = ImageHelper.Decodificar(bytes, 320);
        if (miniatura is null)
        {
            await MessageDialog.InfoAsync(this, "Imagen no válida", "No se pudo cargar la imagen seleccionada.");
            return;
        }

        _imagen = bytes;
        ImagenPreview.Source = miniatura;
        SinImagen.IsVisible = false;
    }

    private async void Guardar_Click(object? sender, RoutedEventArgs e)
    {
        var nombre = (NombreBox.Text ?? string.Empty).Trim();
        if (nombre.Length == 0)
        {
            await MessageDialog.InfoAsync(this, "Campo requerido", "Ingrese un nombre para el ejercicio");
            return;
        }

        if (_imagen is null)
        {
            await MessageDialog.InfoAsync(this, "Campo requerido", "Seleccione una imagen");
            return;
        }

        var dificultad = ComboDificultad.SelectedItem as string ?? Constantes.Dificultades[0];
        Resultado = (nombre, dificultad, _imagen);
        Close(true);
    }

    private void Cancelar_Click(object? sender, RoutedEventArgs e) => Close(false);

    private void Cerrar_Click(object? sender, RoutedEventArgs e) => Close(false);
}
