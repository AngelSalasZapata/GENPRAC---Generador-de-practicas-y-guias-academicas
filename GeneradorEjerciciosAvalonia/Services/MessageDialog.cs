using System.Threading.Tasks;
using Avalonia.Controls;
using GeneradorEjerciciosAvalonia.Views;

namespace GeneradorEjerciciosAvalonia.Services
{
    public static class MessageDialog
    {
        public static async Task InfoAsync(Window owner, string titulo, string mensaje)
        {
            var window = MessageWindow.Info(titulo, mensaje);
            await window.ShowDialog(owner);
        }

        public static async Task<bool> ConfirmAsync(Window owner, string titulo, string mensaje)
        {
            var window = MessageWindow.Confirm(titulo, mensaje);
            return await window.ShowDialog<bool>(owner);
        }
    }
}
