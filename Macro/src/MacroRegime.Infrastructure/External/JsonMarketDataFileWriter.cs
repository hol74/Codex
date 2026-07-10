using System.Text.Json;
using MacroRegime.Application.External;
using MacroRegime.Application.Ports;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Infrastructure.External;

public sealed class JsonMarketDataFileWriter : IMarketDataFileWriter
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web) { WriteIndented = true };

    public async Task<string> WriteAsync(IReadOnlyList<MarketDataObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(observations);
        if (string.IsNullOrWhiteSpace(outputDirectory))
        {
            throw new ArgumentException("Output directory is required.", nameof(outputDirectory));
        }

        Directory.CreateDirectory(outputDirectory);
        var marketRecords = observations.Select(MapMarket).ToArray();
        var record = new JsonDataSnapshotRecord(
            JsonDataSnapshotRecordMapper.CurrentSchemaVersion,
            asOfDate.Value,
            Array.Empty<JsonMacroObservationRecord>(),
            marketRecords);
        var path = Path.Combine(outputDirectory, $"market-data-{asOfDate.Value:yyyy-MM-dd}.json");
        await using var stream = File.Create(path);
        await JsonSerializer.SerializeAsync(stream, record, SerializerOptions, cancellationToken).ConfigureAwait(false);
        return path;
    }

    private static JsonMarketObservationRecord MapMarket(MarketDataObservation observation)
    {
        var meta = MarketDataSeriesCatalog.Resolve(observation.Symbol);
        return new JsonMarketObservationRecord(
            observation.Symbol,
            meta.Name,
            meta.Dimension,
            observation.ObservationDate,
            observation.AvailabilityDate,
            observation.Value,
            "Yahoo Finance",
            observation.Unit,
            meta.ProxyRole);
    }
}
