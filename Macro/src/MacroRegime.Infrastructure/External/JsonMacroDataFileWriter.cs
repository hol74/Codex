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
        return new JsonMacroObservationRecord(
            observation.SeriesCode,
            meta.Name,
            meta.Dimension,
            observation.ObservationDate,
            observation.PublicationDate,
            observation.VintageDate,
            observation.Value,
            "FRED",
            observation.Unit);
    }
}
