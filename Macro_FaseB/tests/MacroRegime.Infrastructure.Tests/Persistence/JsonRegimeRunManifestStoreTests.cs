using System.Text.Json;
using MacroRegime.Application.Ports;
using MacroRegime.Infrastructure.Persistence;

namespace MacroRegime.Infrastructure.Tests.Persistence;

public sealed class JsonRegimeRunManifestStoreTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task UpsertAsync_WritesVersionedManifestSortedByAsOfDateDescending()
    {
        var store = new JsonRegimeRunManifestStore(GetManifestPath());

        await store.UpsertAsync(CreateEntry(new DateOnly(2026, 6, 1), "Slowdown"));
        await store.UpsertAsync(CreateEntry(new DateOnly(2026, 7, 1), "Goldilocks"));

        var json = await File.ReadAllTextAsync(GetManifestPath());
        var record = JsonSerializer.Deserialize<RegimeRunManifestRecord>(json, new JsonSerializerOptions(JsonSerializerDefaults.Web));

        Assert.NotNull(record);
        Assert.Equal(JsonRegimeRunManifestStore.CurrentSchemaVersion, record.SchemaVersion);
        Assert.Collection(
            record.Entries,
            entry => Assert.Equal(new DateOnly(2026, 7, 1), entry.AsOfDate),
            entry => Assert.Equal(new DateOnly(2026, 6, 1), entry.AsOfDate));
    }

    [Fact]
    public async Task UpsertAsync_ReplacesExistingAsOfDateWithoutDuplicatingRows()
    {
        var store = new JsonRegimeRunManifestStore(GetManifestPath());

        await store.UpsertAsync(CreateEntry(new DateOnly(2026, 7, 1), "Goldilocks"));
        await store.UpsertAsync(CreateEntry(new DateOnly(2026, 7, 1), "Reflation"));

        var entries = await store.ListAsync();

        var entry = Assert.Single(entries);
        Assert.Equal("Reflation", entry.PrimaryRegime);
    }

    [Fact]
    public async Task ListAsync_ReturnsEmptyList_WhenManifestDoesNotExist()
    {
        var store = new JsonRegimeRunManifestStore(GetManifestPath());

        var entries = await store.ListAsync();

        Assert.Empty(entries);
    }

    [Fact]
    public async Task ListAsync_RejectsUnsupportedSchemaVersion()
    {
        Directory.CreateDirectory(directoryPath);
        await File.WriteAllTextAsync(GetManifestPath(), """{"schemaVersion":999,"entries":[]}""");
        var store = new JsonRegimeRunManifestStore(GetManifestPath());

        var exception = await Assert.ThrowsAsync<InvalidDataException>(() => store.ListAsync());

        Assert.Contains("unsupported schema version", exception.Message);
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }

    private string GetManifestPath()
    {
        return Path.Combine(directoryPath, "manifest.json");
    }

    private static RegimeRunManifestEntry CreateEntry(DateOnly asOfDate, string primaryRegime)
    {
        return new RegimeRunManifestEntry(
            asOfDate,
            $"memory://regime-run-{asOfDate:yyyy-MM-dd}.json",
            $"memory://macro-regime-report-{asOfDate:yyyy-MM-dd}.md",
            "Imported",
            "Fixture source",
            "samples/macro-data.json",
            "CRS Rule-Based Engine",
            "0.1",
            "CRS Baseline",
            "0.1",
            primaryRegime,
            primaryRegime,
            0.72m,
            0.61m,
            "Confirmed",
            "PartialRebalance",
            0.08m,
            0.0008m,
            0);
    }
}
