using Avalonia.Controls;
using Avalonia.Interactivity;

namespace GeneradorEjerciciosAvalonia.Views;

public partial class MessageWindow : Window
{
    public MessageWindow()
    {
        InitializeComponent();
    }

    public static MessageWindow Info(string titulo, string mensaje)
    {
        var window = new MessageWindow { Title = titulo };
        window.TituloText.Text = titulo;
        window.MensajeText.Text = mensaje;
        window.CancelarBtn.IsVisible = false;
        return window;
    }

    public static MessageWindow Confirm(string titulo, string mensaje)
    {
        var window = new MessageWindow { Title = titulo };
        window.TituloText.Text = titulo;
        window.MensajeText.Text = mensaje;
        window.CancelarBtn.IsVisible = true;
        return window;
    }

    private void Aceptar_Click(object? sender, RoutedEventArgs e) => Close(true);

    private void Cancelar_Click(object? sender, RoutedEventArgs e) => Close(false);
}
