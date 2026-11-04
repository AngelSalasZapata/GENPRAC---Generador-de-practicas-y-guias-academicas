using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Platform.Storage;
using GeneradorEjerciciosAvalonia.Services;
using GeneradorEjerciciosAvalonia.ViewModels;

namespace GeneradorEjerciciosAvalonia.Views;

public partial class CargaMasivaWindow : Window
{
    private readonly CargaMasivaViewModel _vm = new();

    public IReadOnlyList<(string Nombre, string Dificultad, byte[] Imagen)>? Resultado { get; private set; }

    public CargaMasivaWindow()
    {
        InitializeComponent();
        DataContext = _vm;
    }

    public static async Task<IReadOnlyList<(string Nombre, string Dificultad, byte[] Imagen)>?> ShowAsync(Window owner)
    {
        var ventana = new CargaMasivaWindow();
        var aceptado = await ventana.ShowDialog<bool>(owner);
        return aceptado ? ventana.Resultado : null;
    }

    private async void Seleccionar_Click(object? sender, RoutedEventArgs e)
    {
        var archivos = await StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
        {
            Title = "Seleccionar imágenes de ejercicios",
            AllowMultiple = true,
            FileTypeFilter = new[]
            {
                new FilePickerFileType("Imágenes") { Patterns = new[] { "*.png", "*.jpg", "*.jpeg" } },
                FilePickerFileTypes.All,
            },
        });

        if (archivos.Count == 0) return;

        _vm.Limpiar();

        foreach (var archivo in archivos)
        {
            var bytes = await StorageHelpers.LeerBytesAsync(archivo);
            var miniatura = ImageHelper.Decodificar(bytes, 120);
            if (miniatura is null)
            {
                await MessageDialog.InfoAsync(this, "Imagen no válida",
                    $"No se pudo cargar: {archivo.Name}");
                continue;
            }

            var nombre = Path.GetFileNameWithoutExtension(archivo.Name);
            _vm.AgregarFila(new FilaCargaViewModel(_vm, bytes, miniatura, nombre));
        }
    }

    private void Agregar_Click(object? sender, RoutedEventArgs e)
    {
        var resultado = _vm.ConstruirResultado();
        if (resultado.Count == 0) return;

        Resultado = resultado;
        Close(true);
    }

    private void Cancelar_Click(object? sender, RoutedEventArgs e) => Close(false);
}
