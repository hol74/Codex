using System.Text.Json;
using MacroRegime.Infrastructure.External;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class HistoricalDatasetBuilderTests : IDisposable
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "HistoricalDatasetBuilderTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task BuildAsync_MergesMacroAndMarketInputs_AndCalculatesForwardReturns()
    {
        var macroDir = Path.Combine(directoryPath, "macro");
        var marketDir = Path.Combine(directoryPath, "market");
        var outDir = Path.Combine(directoryPath, "out");
        await WriteSnapshotAsync(Path.Combine(macroDir, "macro-data-2026-07-01.json"), Snapshot(
            new DateOnly(2026, 7, 1),
            new[] { Macro("INDPRO_YOY", 2m) },
            Array.Empty<JsonMarketObservationRecord>()));
        await WriteSnapshotAsync(Path.Combine(marketDir, "market-data-2026-07-01.json"), Snapshot(
            new DateOnly(2026, 7, 1),
            Array.Empty<JsonMacroObservationRecord>(),
            new[] { Market("SPY", 100m), Market("GLD", 200m) }));
        await WriteSnapshotAsync(Path.Combine(marketDir, "market-data-2026-07-29.json"), Snapshot(
            new DateOnly(2026, 7, 29),
            Array.Empty<JsonMacroObservationRecord>(),
            new[] { Market("SPY", 110m), Market("GLD", 190m) }));

        var result = await new HistoricalDatasetBuilder().BuildAsync(new BuildHistoricalDatasetCommand(
            new DateOnly(2026, 7, 1),
            new DateOnly(2026, 7, 2),
            macroDir,
            marketDir,
            outDir,
            new[] { 28 }));

        Assert.Equal(1, result.RowCount);
        Assert.Equal(1, result.SkippedDateCount);
        Assert.Equal(2, result.ForwardReturnCount);
        Assert.True(File.Exists(result.OutputPath));

        var record = await ReadDatasetAsync(result.OutputPath);
        var row = Assert.Single(record.Rows);
        Assert.Equal(new DateOnly(2026, 7, 1), row.AsOfDate);
        Assert.Single(row.MacroObservations);
        Assert.Equal(2, row.MarketObservations.Count);
        var spyReturn = Assert.Single(row.ForwardReturns, item => item.Symbol == "SPY");
        Assert.Equal(28, spyReturn.HorizonDays);
        Assert.Equal(new DateOnly(2026, 7, 29), spyReturn.ToDate);
        Assert.Equal(0.1m, spyReturn.ReturnValue);
    }

    [Fact]
    public async Task BuildAsync_UsesFirstAvailableFutureMarketDate_OnOrAfterTarget()
    {
        var macroDir = Path.Combine(directoryPath, "macro2");
        var marketDir = Path.Combine(directoryPath, "market2");
        var outDir = Path.Combine(directoryPath, "out2");
        await WriteSnapshotAsync(Path.Combine(macroDir, "macro-data-2026-07-01.json"), Snapshot(
            new DateOnly(2026, 7, 1),
            new[] { Macro("INDPRO_YOY", 2m) },
            Array.Empty<JsonMarketObservationRecord>()));
        await WriteSnapshotAsync(Path.Combine(marketDir, "market-data-2026-07-01.json"), Snapshot(
            new DateOnly(2026, 7, 1),
            Array.Empty<JsonMacroObservationRecord>(),
            new[] { Market("SPY", 100m) }));
        await WriteSnapshotAsync(Path.Combine(marketDir, "market-data-2026-07-05.json"), Snapshot(
            new DateOnly(2026, 7, 5),
            Array.Empty<JsonMacroObservationRecord>(),
            new[] { Market("SPY", 105m) }));

        var result = await new HistoricalDatasetBuilder().BuildAsync(new BuildHistoricalDatasetCommand(
            new DateOnly(2026, 7, 1),
            new DateOnly(2026, 7, 1),
            macroDir,
            marketDir,
            outDir,
            new[] { 2 }));

        var record = await ReadDatasetAsync(result.OutputPath);
        var forwardReturn = Assert.Single(Assert.Single(record.Rows).ForwardReturns);
        Assert.Equal(new DateOnly(2026, 7, 5), forwardReturn.ToDate);
        Assert.Equal(0.05m, forwardReturn.ReturnValue);
    }

    [Fact]
    public async Task BuildAsync_Throws_WhenSnapshotAsOfDateDoesNotMatchFileName()
    {
        var macroDir = Path.Combine(directoryPath, "macro3");
        var marketDir = Path.Combine(directoryPath, "market3");
        await WriteSnapshotAsync(Path.Combine(macroDir, "macro-data-2026-07-01.json"), Snapshot(
            new DateOnly(2026, 7, 2),
            new[] { Macro("INDPRO_YOY", 2m) },
            Array.Empty<JsonMarketObservationRecord>()));
        await WriteSnapshotAsync(Path.Combine(marketDir, "market-data-2026-07-01.json"), Snapshot(
            new DateOnly(2026, 7, 1),
            Array.Empty<JsonMacroObservationRecord>(),
            new[] { Market("SPY", 100m) }));

        await Assert.ThrowsAsync<InvalidDataException>(() =>
            new HistoricalDatasetBuilder().BuildAsync(new BuildHistoricalDatasetCommand(
                new DateOnly(2026, 7, 1),
                new DateOnly(2026, 7, 1),
                macroDir,
                marketDir,
                Path.Combine(directoryPath, "out3"),
                new[] { 28 })));
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }

    private static JsonDataSnapshotRecord Snapshot(
        DateOnly asOfDate,
        IReadOnlyList<JsonMacroObservationRecord> macro,
        IReadOnlyList<JsonMarketObservationRecord> market)
    {
        return new JsonDataSnapshotRecord(JsonDataSnapshotRecordMapper.CurrentSchemaVersion, asOfDate, macro, market);
    }

    private static JsonMacroObservationRecord Macro(string code, decimal value)
    {
        return new JsonMacroObservationRecord(
            code,
            code,
            "Growth",
            new DateOnly(2026, 6, 30),
            new DateOnly(2026, 7, 1),
            new DateOnly(2026, 7, 1),
            value,
            "Fixture",
            "Index");
    }

    private static JsonMarketObservationRecord Market(string symbol, decimal value)
    {
        return new JsonMarketObservationRecord(
            symbol,
            symbol,
            "Risk",
            new DateOnly(2026, 7, 1),
            new DateOnly(2026, 7, 1),
            value,
            "Fixture",
            "Adjusted close",
            "Test proxy");
    }

    private static async Task WriteSnapshotAsync(string path, JsonDataSnapshotRecord record)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        await File.WriteAllTextAsync(path, JsonSerializer.Serialize(record, SerializerOptions));
    }

    private static async Task<HistoricalDatasetRecord> ReadDatasetAsync(string path)
    {
        await using var stream = File.OpenRead(path);
        return await JsonSerializer.DeserializeAsync<HistoricalDatasetRecord>(stream, SerializerOptions)
            ?? throw new InvalidDataException("Dataset is empty.");
    }
}
