using System;
using System.Collections.Generic;
using System.Text;
using GeneradorEjerciciosAvalonia.Models;
using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;

namespace GeneradorEjerciciosAvalonia.Services
{
    public static class PdfGenerator
    {
        static PdfGenerator()
        {
            QuestPDF.Settings.License = LicenseType.Community;
        }

        private static string TextoSeguro(string? texto)
        {
            return (texto ?? string.Empty).Normalize(NormalizationForm.FormC);
        }

        public static string GenerarPdfEjercicios(
            IReadOnlyList<int> ejerciciosIds,
            string filename,
            ConfiguracionDocumento documento,
            Func<int, byte[]?> obtenerImagen)
        {
            documento ??= new ConfiguracionDocumento();

            var titulo = TextoSeguro(documento.Titulo);
            var autor = TextoSeguro(documento.Autor);
            var etiqueta = TextoSeguro(documento.Etiqueta);
            var espacioExtraMm = (float)(Math.Max(0.0, documento.EspacioCm) * 10.0);

            var imagenes = new List<(int Indice, byte[] Datos)>();
            for (var i = 0; i < ejerciciosIds.Count; i++)
            {
                var datos = obtenerImagen(ejerciciosIds[i]);
                if (datos is { Length: > 0 })
                {
                    imagenes.Add((i, datos));
                }
            }

            Document.Create(container =>
            {
                container.Page(page =>
                {
                    page.Size(PageSizes.A4);
                    page.Margin(10, Unit.Millimetre);
                    page.PageColor(Colors.White);
                    page.DefaultTextStyle(x => x.FontSize(10).FontFamily("Arial").FontColor(Colors.Black));

                    page.Header().PaddingTop(4).Column(col =>
                    {
                        col.Item().AlignCenter().Text(titulo).Bold().FontSize(14);
                        col.Item().AlignCenter().Text($"Por: {autor}").FontSize(10);
                        col.Item().PaddingTop(5);
                    });

                    page.Content().PaddingTop(8).Table(table =>
                    {
                        table.ColumnsDefinition(columns =>
                        {
                            columns.RelativeColumn();
                            columns.RelativeColumn();
                        });

                        var numero = 0;
                        foreach (var (_, datos) in imagenes)
                        {
                            numero++;
                            var etiquetaActual = $"{etiqueta} {numero}";
                            table.Cell().Padding(5, Unit.Millimetre).PaddingBottom(5 + espacioExtraMm, Unit.Millimetre).Column(cell =>
                            {
                                cell.Item().Text(etiquetaActual).Bold().FontSize(10);
                                cell.Item().PaddingTop(3, Unit.Millimetre).Image(datos).FitWidth();
                            });
                        }
                    });

                    page.Footer().AlignCenter().Text(text =>
                    {
                        text.Span("Página ");
                        text.CurrentPageNumber();
                    });
                });
            }).GeneratePdf(filename);

            return filename;
        }
    }
}
