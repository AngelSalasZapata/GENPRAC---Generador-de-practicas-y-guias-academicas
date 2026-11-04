using Avalonia.Controls;

namespace GeneradorEjerciciosAvalonia.Views;

public partial class ProgressWindow : Window
{
    public ProgressWindow()
    {
        InitializeComponent();
    }

    public ProgressWindow(string titulo) : this()
    {
        Title = titulo;
    }

    public void Actualizar(string mensaje, double progreso)
    {
        EstadoText.Text = mensaje;
        Barra.Value = progreso;
    }
}
