using MacroRegime.Application.External;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.External;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class JsonMarketDataFileWriterTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "JsonMarketDataFileWriterTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task WriteAsync_WritesFile_NamedMarketDataDateJson()
    {
        var writer = new JsonMarketDataFileWriter();
        var outDir = Path.Combine(directoryPath, "out");
        Directory.CreateDirectory(outDir);
        var observations = new[]
        {
            new MarketDataObservation("SPY", "SPY", new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), 512.34m, "Adjusted close"),
        };

        var path = await writer.WriteAsync(observations, new AsOfDate(new DateOnly(2026, 7, 1)), outDir);

        Assert.Equal(Path.Combine(outDir, "market-data-2026-07-01.json"), path);
    }

    [Fact]
    public async Task WriteAsync_SerializesMarketObservations_AndEmptyMacroArray()
    {
        var writer = new JsonMarketDataFileWriter();
        var outDir = Path.Combine(directoryPath, "out");
        Directory.CreateDirectory(outDir);
        var observations = new[]
        {
            new MarketDataObservation("SPY", "SPY", new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), 512.34m, "Adjusted close"),
        };

        var path = await writer.WriteAsync(observations, new AsOfDate(new DateOnly(2026, 7, 1)), outDir);
        var json = await File.ReadAllTextAsync(path);

        Assert.Contains("\"macroObservations\": []", json);
        Assert.Contains("\"marketObservations\": [", json);
        Assert.Contains("\"symbol\": \"SPY\"", json);
        Assert.Contains("\"proxyRole\": \"US equity proxy\"", json);
    }

    [Fact]
    public async Task WriteAsync_RoundTrips_ThroughJsonDataSnapshotProvider()
    {
        var writer = new JsonMarketDataFileWriter();
        var outDir = Path.Combine(directoryPath, "out");
        Directory.CreateDirectory(outDir);
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var observations = new[]
        {
            new MarketDataObservation("SPY", "SPY", new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), 512.34m, "Adjusted close"),
            new MarketDataObservation("GLD", "GLD", new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), 221.10m, "Adjusted close"),
        };

        var path = await writer.WriteAsync(observations, asOf, outDir);
        var provider = new JsonDataSnapshotProvider(path, strict: true);
        var snapshot = await provider.GetSnapshotAsync(asOf);

        Assert.NotNull(snapshot);
        Assert.Equal(2, snapshot!.MarketObservations.Count);
        Assert.Empty(snapshot.MacroObservations);
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }
}
