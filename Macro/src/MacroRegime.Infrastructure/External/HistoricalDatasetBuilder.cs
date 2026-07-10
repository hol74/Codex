using System.Globalization;
using System.Text.Json;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Infrastructure.External;

public sealed record BuildHistoricalDatasetCommand(
    DateOnly From,
    DateOnly To,
    string MacroDataDirectory,
    string MarketDataDirectory,
    string OutputDirectory,
    IReadOnlyList<int> ForwardReturnHorizonsDays);

public sealed record BuildHistoricalDatasetResult(
    string OutputPath,
    int RowCount,
    int SkippedDateCount,
    int ForwardReturnCount);

public sealed record HistoricalDatasetRecord(
    int SchemaVersion,
    DateOnly From,
    DateOnly To,
    IReadOnlyList<int> ForwardReturnHorizonsDays,
    IReadOnlyList<HistoricalDatasetRowRecord> Rows);

public sealed record HistoricalDatasetRowRecord(
    DateOnly AsOfDate,
    IReadOnlyList<JsonMacroObservationRecord> MacroObservations,
    IReadOnlyList<JsonMarketObservationRecord> MarketObservations,
    IReadOnlyList<HistoricalForwardReturnRecord> ForwardReturns);

public sealed record HistoricalForwardReturnRecord(
    string Symbol,
    int HorizonDays,
    DateOnly FromDate,
    DateOnly ToDate,
    decimal StartValue,
    decimal EndValue,
    decimal ReturnValue);

public sealed class HistoricalDatasetBuilder
{
    private const int CurrentSchemaVersion = 1;
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    public async Task<BuildHistoricalDatasetResult> BuildAsync(
        BuildHistoricalDatasetCommand command,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        Validate(command);

        var marketSnapshots = await ReadSnapshotDirectoryAsync(command.MarketDataDirectory, "market-data-", cancellationToken).ConfigureAwait(false);
        var rows = new List<HistoricalDatasetRowRecord>();
        var skipped = 0;
        var forwardReturnCount = 0;

        for (var date = command.From; date <= command.To; date = date.AddDays(1))
        {
            cancellationToken.ThrowIfCancellationRequested();
            var macroPath = Path.Combine(command.MacroDataDirectory, $"macro-data-{date:yyyy-MM-dd}.json");
            var marketPath = Path.Combine(command.MarketDataDirectory, $"market-data-{date:yyyy-MM-dd}.json");
            if (!File.Exists(macroPath) || !File.Exists(marketPath))
            {
                skipped++;
                continue;
            }

            var macroRecord = await ReadSnapshotAsync(macroPath, cancellationToken).ConfigureAwait(false);
            var marketRecord = await ReadSnapshotAsync(marketPath, cancellationToken).ConfigureAwait(false);
            EnsureAsOfDate(macroRecord, date, macroPath);
            EnsureAsOfDate(marketRecord, date, marketPath);

            var forwardReturns = BuildForwardReturns(
                date,
                marketRecord.MarketObservations ?? Array.Empty<JsonMarketObservationRecord>(),
                marketSnapshots,
                command.ForwardReturnHorizonsDays);
            forwardReturnCount += forwardReturns.Count;

            rows.Add(new HistoricalDatasetRowRecord(
                date,
                macroRecord.MacroObservations ?? Array.Empty<JsonMacroObservationRecord>(),
                marketRecord.MarketObservations ?? Array.Empty<JsonMarketObservationRecord>(),
                forwardReturns));
        }

        var record = new HistoricalDatasetRecord(
            CurrentSchemaVersion,
            command.From,
            command.To,
            command.ForwardReturnHorizonsDays.OrderBy(day => day).ToArray(),
            rows);

        Directory.CreateDirectory(command.OutputDirectory);
        var outputPath = Path.Combine(command.OutputDirectory, $"historical-dataset-{command.From:yyyy-MM-dd}-{command.To:yyyy-MM-dd}.json");
        await using var stream = File.Create(outputPath);
        await JsonSerializer.SerializeAsync(stream, record, SerializerOptions, cancellationToken).ConfigureAwait(false);

        return new BuildHistoricalDatasetResult(outputPath, rows.Count, skipped, forwardReturnCount);
    }

    private static void Validate(BuildHistoricalDatasetCommand command)
    {
        if (command.From > command.To)
        {
            throw new ArgumentException("Dataset from date must be on or before dataset to date.", nameof(command));
        }

        if (string.IsNullOrWhiteSpace(command.MacroDataDirectory))
        {
            throw new ArgumentException("Macro data directory is required.", nameof(command));
        }

        if (string.IsNullOrWhiteSpace(command.MarketDataDirectory))
        {
            throw new ArgumentException("Market data directory is required.", nameof(command));
        }

        if (string.IsNullOrWhiteSpace(command.OutputDirectory))
        {
            throw new ArgumentException("Output directory is required.", nameof(command));
        }

        if (command.ForwardReturnHorizonsDays.Count == 0 || command.ForwardReturnHorizonsDays.Any(day => day <= 0))
        {
            throw new ArgumentException("At least one positive forward return horizon is required.", nameof(command));
        }
    }

    private static async Task<SortedDictionary<DateOnly, JsonDataSnapshotRecord>> ReadSnapshotDirectoryAsync(
        string directory,
        string prefix,
        CancellationToken cancellationToken)
    {
        var snapshots = new SortedDictionary<DateOnly, JsonDataSnapshotRecord>();
        if (!Directory.Exists(directory))
        {
            return snapshots;
        }

        foreach (var path in Directory.EnumerateFiles(directory, $"{prefix}*.json"))
        {
            cancellationToken.ThrowIfCancellationRequested();
            var date = ParseDateFromFileName(path, prefix);
            if (date is null)
            {
                continue;
            }

            snapshots[date.Value] = await ReadSnapshotAsync(path, cancellationToken).ConfigureAwait(false);
        }

        return snapshots;
    }

    private static async Task<JsonDataSnapshotRecord> ReadSnapshotAsync(string path, CancellationToken cancellationToken)
    {
        await using var stream = File.OpenRead(path);
        try
        {
            return await JsonSerializer.DeserializeAsync<JsonDataSnapshotRecord>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false)
                ?? throw new InvalidDataException($"Data snapshot file '{path}' is empty.");
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException($"Data snapshot file '{path}' is not valid JSON.", exception);
        }
    }

    private static DateOnly? ParseDateFromFileName(string path, string prefix)
    {
        var fileName = Path.GetFileNameWithoutExtension(path);
        if (!fileName.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        var dateText = fileName[prefix.Length..];
        return DateOnly.TryParseExact(dateText, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var date)
            ? date
            : null;
    }

    private static void EnsureAsOfDate(JsonDataSnapshotRecord record, DateOnly expected, string path)
    {
        if (record.SchemaVersion != JsonDataSnapshotRecordMapper.CurrentSchemaVersion)
        {
            throw new InvalidDataException($"Data snapshot file '{path}' has unsupported schema version {record.SchemaVersion}.");
        }

        if (record.AsOfDate != expected)
        {
            throw new InvalidDataException($"Data snapshot file '{path}' has as-of date {record.AsOfDate:yyyy-MM-dd}; expected {expected:yyyy-MM-dd}.");
        }
    }

    private static IReadOnlyList<HistoricalForwardReturnRecord> BuildForwardReturns(
        DateOnly asOfDate,
        IReadOnlyList<JsonMarketObservationRecord> currentObservations,
        SortedDictionary<DateOnly, JsonDataSnapshotRecord> marketSnapshots,
        IReadOnlyList<int> horizons)
    {
        var currentBySymbol = currentObservations
            .Where(observation => !string.IsNullOrWhiteSpace(observation.Symbol))
            .GroupBy(observation => observation.Symbol!, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(group => group.Key, group => group.First(), StringComparer.OrdinalIgnoreCase);
        var returns = new List<HistoricalForwardReturnRecord>();

        foreach (var horizon in horizons.OrderBy(day => day))
        {
            var targetDate = asOfDate.AddDays(horizon);
            var future = marketSnapshots.FirstOrDefault(pair => pair.Key >= targetDate);
            if (future.Value is null)
            {
                continue;
            }

            var futureBySymbol = (future.Value.MarketObservations ?? Array.Empty<JsonMarketObservationRecord>())
                .Where(observation => !string.IsNullOrWhiteSpace(observation.Symbol))
                .GroupBy(observation => observation.Symbol!, StringComparer.OrdinalIgnoreCase)
                .ToDictionary(group => group.Key, group => group.First(), StringComparer.OrdinalIgnoreCase);

            foreach (var (symbol, current) in currentBySymbol.OrderBy(pair => pair.Key, StringComparer.OrdinalIgnoreCase))
            {
                if (current.Value == 0m || !futureBySymbol.TryGetValue(symbol, out var futureObservation))
                {
                    continue;
                }

                var returnValue = (futureObservation.Value / current.Value) - 1m;
                returns.Add(new HistoricalForwardReturnRecord(
                    symbol,
                    horizon,
                    asOfDate,
                    future.Key,
                    current.Value,
                    futureObservation.Value,
                    decimal.Round(returnValue, 8, MidpointRounding.ToEven)));
            }
        }

        return returns;
    }
}
