using MacroRegime.Application.External;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.External;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class JsonMacroDataFileWriterTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "JsonMacroDataFileWriterTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task WriteAsync_CreatesDirectory_IfMissing()
    {
        var writer = new JsonMacroDataFileWriter();
        var outDir = Path.Combine(directoryPath, "nested", "out");
        var observations = new[]
        {
            new FredObservation("INDPRO", "INDPRO_YOY", new DateOnly(2026, 6, 30), new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), 2.0m, "Percent change"),
        };

        var path = await writer.WriteAsync(observations, new AsOfDate(new DateOnly(2026, 7, 1)), outDir);

        Assert.True(Directory.Exists(outDir));
        Assert.True(File.Exists(path));
    }

    [Fact]
    public async Task WriteAsync_WritesFile_NamedMacroDataDateJson()
    {
        var writer = new JsonMacroDataFileWriter();
        var outDir = Path.Combine(directoryPath, "out");
        Directory.CreateDirectory(outDir);
        var observations = new[]
        {
            new FredObservation("INDPRO", "INDPRO_YOY", new DateOnly(2026, 6, 30), new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), 2.0m, "Percent change"),
        };

        var path = await writer.WriteAsync(observations, new AsOfDate(new DateOnly(2026, 7, 1)), outDir);

        Assert.Equal(Path.Combine(outDir, "macro-data-2026-07-01.json"), path);
    }

    [Fact]
    public async Task WriteAsync_SerializesSchemaVersion1_AndCamelCase()
    {
        var writer = new JsonMacroDataFileWriter();
        var outDir = Path.Combine(directoryPath, "out");
        Directory.CreateDirectory(outDir);
        var observations = new[]
        {
            new FredObservation("INDPRO", "INDPRO_YOY", new DateOnly(2026, 6, 30), new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), 2.0m, "Percent change"),
        };

        var path = await writer.WriteAsync(observations, new AsOfDate(new DateOnly(2026, 7, 1)), outDir);
        var json = await File.ReadAllTextAsync(path);

        Assert.Contains("\"schemaVersion\": 1", json);
        Assert.Contains("\"asOfDate\": \"2026-07-01\"", json);
        Assert.Contains("\"seriesCode\": \"INDPRO_YOY\"", json);
        Assert.Contains("\"macroObservations\": [", json);
        Assert.Contains("\"marketObservations\": []", json);
    }

    [Fact]
    public async Task WriteAsync_RoundTrips_ThroughJsonDataSnapshotProvider()
    {
        var writer = new JsonMacroDataFileWriter();
        var outDir = Path.Combine(directoryPath, "out");
        Directory.CreateDirectory(outDir);
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var observations = new[]
        {
            new FredObservation("INDPRO", "INDPRO_YOY", new DateOnly(2026, 6, 30), new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), 2.0m, "Percent change"),
            new FredObservation("VIXCLS", "VIX", new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 1), 18.0m, "Index"),
        };

        var path = await writer.WriteAsync(observations, asOf, outDir);
        var provider = new JsonDataSnapshotProvider(path, strict: true);
        var snapshot = await provider.GetSnapshotAsync(asOf);

        Assert.NotNull(snapshot);
        Assert.Equal(asOf.Value, snapshot!.AsOfDate.Value);
        Assert.Equal(2, snapshot.MacroObservations.Count);
        Assert.Empty(snapshot.MarketObservations);
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }
}
