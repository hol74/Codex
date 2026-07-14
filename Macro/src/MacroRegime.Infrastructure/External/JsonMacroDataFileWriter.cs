using System.Text.Json;
using MacroRegime.Application.External;
using MacroRegime.Application.Ports;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Infrastructure.External;

public sealed class JsonMacroDataFileWriter : IMacroDataFileWriter
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web) { WriteIndented = true };

    public async Task<string> WriteAsync(IReadOnlyList<FredObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(observations);
        if (string.IsNullOrWhiteSpace(outputDirectory))
        {
            throw new ArgumentException("Output directory is required.", nameof(outputDirectory));
        }

        Directory.CreateDirectory(outputDirectory);
        var macroRecords = observations.Select(MapMacro).ToArray();
        var record = new JsonDataSnapshotRecord(
            JsonDataSnapshotRecordMapper.CurrentSchemaVersion,
            asOfDate.Value,
            macroRecords,
            Array.Empty<JsonMarketObservationRecord>());
        var path = Path.Combine(outputDirectory, $"macro-data-{asOfDate.Value:yyyy-MM-dd}.json");
        await using var stream = File.Create(path);
        await JsonSerializer.SerializeAsync(stream, record, SerializerOptions, cancellationToken).ConfigureAwait(false);
        return path;
    }

    private static JsonMacroObservationRecord MapMacro(FredObservation observation)
    {
        var meta = FredSeriesCatalog.Resolve(observation.SeriesCode);
        var usesAlternateProvider = !string.Equals(observation.SeriesId, meta.FredSeriesId, StringComparison.OrdinalIgnoreCase);
        var isHistoricalProxy = usesAlternateProvider
            && string.Equals(observation.SeriesCode, "HY_OAS", StringComparison.OrdinalIgnoreCase);
        var source = observation.SeriesId.StartsWith("DERIVED:MARKET:", StringComparison.OrdinalIgnoreCase)
            ? "Derived:Yahoo Finance"
            : observation.SeriesId.StartsWith("DERIVED:FRED:", StringComparison.OrdinalIgnoreCase)
                ? "Derived:FRED"
                : usesAlternateProvider ? $"FRED:{observation.SeriesId}" : "FRED";
        return new JsonMacroObservationRecord(
            observation.SeriesCode,
            isHistoricalProxy ? "Baa corporate minus 10-year Treasury credit-spread proxy" : meta.Name,
            meta.Dimension,
            observation.ObservationDate,
            observation.PublicationDate,
            observation.VintageDate,
            observation.Value,
            source,
            observation.Unit);
    }
}
