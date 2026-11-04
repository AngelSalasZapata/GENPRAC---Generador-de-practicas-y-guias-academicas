using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Media.Imaging;
using Microsoft.Data.Sqlite;

namespace GeneradorEjerciciosAvalonia.Services
{
    public sealed class DatabaseService
    {
        private readonly string _dbPath;
        private readonly string _connectionString;

        public string DbPath => _dbPath;

        public DatabaseService() : this(ResolveDefaultPath()) { }

        public DatabaseService(string dbPath)
        {
            _dbPath = dbPath;
            _connectionString = new SqliteConnectionStringBuilder
            {
                DataSource = dbPath
            }.ToString();
            Initialize();
        }

        private static string ResolveDefaultPath()
        {
            var baseDir = AppContext.BaseDirectory;
            return Path.Combine(baseDir, "ejercicios.db");
        }

        private SqliteConnection Open()
        {
            var connection = new SqliteConnection(_connectionString);
            connection.Open();
            using var pragma = connection.CreateCommand();
            pragma.CommandText = "PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL;";
            pragma.ExecuteNonQuery();
            return connection;
        }

        private void Initialize()
        {
            using var connection = Open();

            // Tabla principal
            using var cmdCreate = connection.CreateCommand();
            cmdCreate.CommandText = @"
                CREATE TABLE IF NOT EXISTS ejercicios
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     nombre TEXT,
                     dificultad TEXT,
                     imagen BLOB);
                CREATE INDEX IF NOT EXISTS idx_ejercicios_dificultad ON ejercicios(dificultad);";
            cmdCreate.ExecuteNonQuery();

            // Migración: agregar columna miniatura si aún no existe
            var cols = new System.Collections.Generic.HashSet<string>(StringComparer.OrdinalIgnoreCase);
            using var cmdInfo = connection.CreateCommand();
            cmdInfo.CommandText = "PRAGMA table_info(ejercicios)";
            using var reader = cmdInfo.ExecuteReader();
            while (reader.Read()) cols.Add(reader.GetString(1));
            reader.Close();

            if (!cols.Contains("miniatura"))
            {
                using var cmdAlter = connection.CreateCommand();
                cmdAlter.CommandText = "ALTER TABLE ejercicios ADD COLUMN miniatura BLOB";
                cmdAlter.ExecuteNonQuery();
            }
        }

        public void AgregarEjercicio(string nombre, string dificultad, byte[] imagen)
        {
            var miniatura = GenerarMiniatura(imagen);
            using var connection = Open();
            using var command = connection.CreateCommand();
            command.CommandText =
                "INSERT INTO ejercicios (nombre, dificultad, imagen, miniatura) VALUES ($nombre, $dificultad, $imagen, $miniatura)";
            command.Parameters.AddWithValue("$nombre", nombre ?? string.Empty);
            command.Parameters.AddWithValue("$dificultad", dificultad ?? string.Empty);
            command.Parameters.AddWithValue("$imagen", (object?)imagen ?? DBNull.Value);
            command.Parameters.AddWithValue("$miniatura", (object?)miniatura ?? DBNull.Value);
            command.ExecuteNonQuery();
        }

        public void AgregarEjercicios(IReadOnlyList<(string Nombre, string Dificultad, byte[] Imagen)> ejercicios)
        {
            if (ejercicios.Count == 0) return;

            using var connection = Open();
            using var transaction = connection.BeginTransaction();
            try
            {
                using var command = connection.CreateCommand();
                command.Transaction = transaction;
                command.CommandText =
                    "INSERT INTO ejercicios (nombre, dificultad, imagen, miniatura) VALUES ($nombre, $dificultad, $imagen, $miniatura)";
                var pNombre    = command.Parameters.Add("$nombre", SqliteType.Text);
                var pDificultad = command.Parameters.Add("$dificultad", SqliteType.Text);
                var pImagen    = command.Parameters.Add("$imagen", SqliteType.Blob);
                var pMiniatura = command.Parameters.Add("$miniatura", SqliteType.Blob);

                foreach (var (nombre, dificultad, imagen) in ejercicios)
                {
                    pNombre.Value    = nombre ?? string.Empty;
                    pDificultad.Value = dificultad ?? string.Empty;
                    pImagen.Value    = (object?)imagen ?? DBNull.Value;
                    pMiniatura.Value = (object?)GenerarMiniatura(imagen) ?? DBNull.Value;
                    command.ExecuteNonQuery();
                }

                transaction.Commit();
            }
            catch
            {
                transaction.Rollback();
                throw;
            }
        }

        /// <summary>
        /// Genera una miniatura JPEG reducida a 320 px de ancho usando SkiaSharp vía Avalonia.
        /// Devuelve null si los datos son inválidos o están vacíos.
        /// </summary>
        private static byte[]? GenerarMiniatura(byte[]? imagen)
        {
            if (imagen is null || imagen.Length == 0) return null;
            try
            {
                using var ms = new MemoryStream(imagen, writable: false);
                var bmp = Avalonia.Media.Imaging.Bitmap.DecodeToWidth(ms, 320);
                using var out_ = new MemoryStream();
#pragma warning disable CS0618 // Bitmap.Save(Stream) — API única disponible en esta versión de Avalonia
                bmp.Save(out_);
#pragma warning restore CS0618
                return out_.ToArray();
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// Devuelve la miniatura si existe, o la imagen completa escalada en memoria.
        /// Nunca trae el BLOB completo a menos que no haya miniatura.
        /// </summary>
        public byte[]? ObtenerMiniatura(int id)
        {
            using var connection = Open();
            using var command = connection.CreateCommand();
            command.CommandText = "SELECT miniatura, imagen FROM ejercicios WHERE id = $id";
            command.Parameters.AddWithValue("$id", id);
            using var reader = command.ExecuteReader();
            if (!reader.Read()) return null;

            if (!reader.IsDBNull(0)) return reader.GetFieldValue<byte[]>(0);
            if (!reader.IsDBNull(1))
            {
                var full = reader.GetFieldValue<byte[]>(1);
                // Generar y persistir miniatura
                var mini = GenerarMiniatura(full);
                if (mini != null)
                {
                    reader.Close();
                    using var upd = connection.CreateCommand();
                    upd.CommandText = "UPDATE ejercicios SET miniatura = $m WHERE id = $id";
                    upd.Parameters.AddWithValue("$m", mini);
                    upd.Parameters.AddWithValue("$id", id);
                    try { upd.ExecuteNonQuery(); } catch { /* non-fatal */ }
                    return mini;
                }
                return full;
            }
            return null;
        }

        /// <summary>Lista ligera (id, nombre, dificultad) sin cargar los BLOB de imagen.</summary>
        public List<Models.EjercicioResumen> ObtenerEjerciciosLista()
        {
            var result = new List<Models.EjercicioResumen>();
            using var connection = Open();
            using var command = connection.CreateCommand();
            command.CommandText = "SELECT id, nombre, dificultad FROM ejercicios";
            using var reader = command.ExecuteReader();
            while (reader.Read())
            {
                result.Add(new Models.EjercicioResumen
                {
                    Id = reader.GetInt32(0),
                    Nombre = reader.IsDBNull(1) ? string.Empty : reader.GetString(1),
                    Dificultad = reader.IsDBNull(2) ? string.Empty : reader.GetString(2),
                });
            }
            return result;
        }

        public byte[]? ObtenerImagen(int id)
        {
            using var connection = Open();
            using var command = connection.CreateCommand();
            command.CommandText = "SELECT imagen FROM ejercicios WHERE id = $id";
            command.Parameters.AddWithValue("$id", id);
            var result = command.ExecuteScalar();
            return result is byte[] bytes ? bytes : null;
        }

        public List<int> ObtenerIdsPorDificultad(string dificultad)
        {
            var result = new List<int>();
            using var connection = Open();
            using var command = connection.CreateCommand();
            command.CommandText = "SELECT id FROM ejercicios WHERE dificultad = $dificultad";
            command.Parameters.AddWithValue("$dificultad", dificultad);
            using var reader = command.ExecuteReader();
            while (reader.Read())
            {
                result.Add(reader.GetInt32(0));
            }
            return result;
        }

        public List<int> ObtenerEjerciciosPorDificultad(string dificultad, int cantidad)
        {
            if (cantidad <= 0) return new List<int>();
            var result = new List<int>();
            using var connection = Open();
            using var command = connection.CreateCommand();
            command.CommandText = "SELECT id FROM ejercicios WHERE dificultad = $dificultad ORDER BY RANDOM() LIMIT $cantidad";
            command.Parameters.AddWithValue("$dificultad", dificultad);
            command.Parameters.AddWithValue("$cantidad", cantidad);
            using var reader = command.ExecuteReader();
            while (reader.Read())
            {
                result.Add(reader.GetInt32(0));
            }
            return result;
        }

        public Dictionary<string, int> ContarPorDificultad()
        {
            var result = new Dictionary<string, int>();
            using var connection = Open();
            using var command = connection.CreateCommand();
            command.CommandText = "SELECT dificultad, COUNT(*) FROM ejercicios GROUP BY dificultad";
            using var reader = command.ExecuteReader();
            while (reader.Read())
            {
                var key = reader.IsDBNull(0) ? string.Empty : reader.GetString(0);
                result[key] = reader.GetInt32(1);
            }
            return result;
        }

        public void EliminarEjercicio(int id)
        {
            using var connection = Open();
            using var command = connection.CreateCommand();
            command.CommandText = "DELETE FROM ejercicios WHERE id = $id";
            command.Parameters.AddWithValue("$id", id);
            command.ExecuteNonQuery();
        }
    }
}
