using System;
using System.IO;
using Avalonia.Media.Imaging;

namespace GeneradorEjerciciosAvalonia.Services
{
    public static class ImageHelper
    {
        public static Bitmap? Decodificar(byte[]? datos, int anchoMaximo = 0)
        {
            if (datos is null || datos.Length == 0)
            {
                return null;
            }

            try
            {
                using var stream = new MemoryStream(datos, writable: false);
                return anchoMaximo > 0
                    ? Bitmap.DecodeToWidth(stream, anchoMaximo)
                    : new Bitmap(stream);
            }
            catch
            {
                return null;
            }
        }
    }
}
