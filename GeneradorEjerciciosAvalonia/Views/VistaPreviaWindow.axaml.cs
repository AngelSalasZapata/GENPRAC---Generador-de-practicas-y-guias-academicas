using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Media;
using GeneradorEjerciciosAvalonia.Models;
using GeneradorEjerciciosAvalonia.Services;

namespace GeneradorEjerciciosAvalonia.Views;

public partial class VistaPreviaWindow : Window
{
    public VistaPreviaWindow()
    {
        InitializeComponent();
    }

    public static async Task ShowAsync(Window owner, Ejercicio ejercicio)
    {
        var ventana = new VistaPreviaWindow
        {
            Title = $"Vista Previa: {ejercicio.Nombre}",
        };

        ventana.NombreText.Text = ejercicio.Nombre;
        ventana.DificultadText.Text = $"• {ejercicio.Dificultad}";
        ventana.DificultadText.Foreground = Brush.Parse(Constantes.ColorDe(ejercicio.Dificultad));
        ventana.DificultadBadge.Background = Brush.Parse(Constantes.FondoDe(ejercicio.Dificultad));

        var imagen = ImageHelper.Decodificar(ejercicio.Imagen, 560);
        if (imagen is not null)
        {
            ventana.ImagenPreview.Source = imagen;
        }
        else
        {
            ventana.ImagenPreview.IsVisible = false;
            ventana.ImagenError.IsVisible = true;
        }

        await ventana.ShowDialog(owner);
    }

    private void Cerrar_Click(object? sender, RoutedEventArgs e) => Close();
}
