using System.IO;
using System.Threading.Tasks;
using Avalonia.Platform.Storage;

namespace GeneradorEjerciciosAvalonia.Services
{
    public static class StorageHelpers
    {
        public static async Task<byte[]> LeerBytesAsync(IStorageFile archivo)
        {
            await using var origen = await archivo.OpenReadAsync();
            using var memoria = new MemoryStream();
            await origen.CopyToAsync(memoria);
            return memoria.ToArray();
        }
    }
}
