using System.Text.Json;
using MacroRegime.Application.Runs;
using MacroRegime.Infrastructure.Persistence;

namespace MacroRegime.Infrastructure.Tests.Persistence;

public sealed class JsonRegimeRunStoreTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task SaveAsync_WritesMappedRegimeRunRecordAsJson()
    {
        var document = CreateDocument();
        var store = new JsonRegimeRunStore(directoryPath);

        await store.SaveAsync(document);

        var path = store.GetPath(document.AsOfDate);
        Assert.True(File.Exists(path));

        var json = await File.ReadAllTextAsync(path);
        var record = JsonSerializer.Deserialize<RegimeRunRecord>(json, new JsonSerializerOptions(JsonSerializerDefaults.Web));

        Assert.NotNull(record);
        Assert.Equal(RegimeRunRecordMapper.CurrentSchemaVersion, record.SchemaVersion);
        Assert.Equal(document.AsOfDate, record.AsOfDate);
        Assert.Equal("Goldilocks", record.PrimaryRegime);
        Assert.Equal("Goldilocks", record.OperationalRegime);
        Assert.Equal(2, record.Probabilities.Count);
        Assert.Equal("GROWTH_MOM", Assert.Single(record.FeatureScores).FeatureCode);
        Assert.NotNull(record.Allocation);
        Assert.Equal("PartialRebalance", record.Allocation.Suggestion);
        Assert.NotNull(record.DataSource);
        Assert.Equal("Imported", record.DataSource.Kind);
    }

    [Fact]
    public async Task LoadAsync_RoundTripsSavedDocument()
    {
        var document = CreateDocument();
        var store = new JsonRegimeRunStore(directoryPath);

        await store.SaveAsync(document);
        var loaded = await store.LoadAsync(document.AsOfDate);

        Assert.NotNull(loaded);
        Assert.Equal(JsonSerializer.Serialize(document), JsonSerializer.Serialize(loaded));
    }

    [Fact]
    public async Task LoadAsync_ReturnsNull_WhenRunFileDoesNotExist()
    {
        var store = new JsonRegimeRunStore(directoryPath);

        var loaded = await store.LoadAsync(new DateOnly(2026, 7, 1));

        Assert.Null(loaded);
    }

    [Fact]
    public async Task LoadAsync_ReadsSchemaVersionOneRuns_WithoutAllocationAndDataSource()
    {
        Directory.CreateDirectory(directoryPath);
        var asOfDate = new DateOnly(2026, 7, 1);
        var legacyJson = """
        {
          "schemaVersion": 1,
          "asOfDate": "2026-07-01",
          "modelName": "CRS Rule-Based Engine",
          "modelVersion": "0.1",
          "featureSetName": "CRS Baseline",
          "featureSetVersion": "0.1",
          "primaryRegime": "Goldilocks",
          "operationalRegime": "Goldilocks",
          "confidence": 0.7,
          "compositeScore": 0.65,
          "status": "Confirmed",
          "probabilities": [
            { "regime": "Goldilocks", "probability": 0.7, "rank": 1 },
            { "regime": "Reflation", "probability": 0.3, "rank": 2 }
          ],
          "featureScores": [],
          "explanations": [],
          "warnings": []
        }
        """;
        var store = new JsonRegimeRunStore(directoryPath);
        await File.WriteAllTextAsync(store.GetPath(asOfDate), legacyJson);

        var loaded = await store.LoadAsync(asOfDate);

        Assert.NotNull(loaded);
        Assert.Equal("Goldilocks", loaded.PrimaryRegime);
        Assert.Null(loaded.Allocation);
        Assert.Null(loaded.DataSource);
    }

    [Fact]
    public async Task LoadAsync_Throws_WhenSchemaVersionIsUnsupported()
    {
        Directory.CreateDirectory(directoryPath);
        var asOfDate = new DateOnly(2026, 7, 1);
        var store = new JsonRegimeRunStore(directoryPath);
        var record = RegimeRunRecordMapper.FromDocument(CreateDocument()) with { SchemaVersion = 99 };
        await File.WriteAllTextAsync(
            store.GetPath(asOfDate),
            JsonSerializer.Serialize(record, new JsonSerializerOptions(JsonSerializerDefaults.Web)));

        await Assert.ThrowsAsync<InvalidDataException>(() => store.LoadAsync(asOfDate));
    }

    [Fact]
    public async Task SaveAsync_IsIdempotentForSameDocumentAndAsOfDate()
    {
        var document = CreateDocument();
        var store = new JsonRegimeRunStore(directoryPath);

        await store.SaveAsync(document);
        var path = store.GetPath(document.AsOfDate);
        var firstContent = await File.ReadAllTextAsync(path);

        await store.SaveAsync(document);
        var secondContent = await File.ReadAllTextAsync(path);

        Assert.Equal(firstContent, secondContent);
        Assert.Single(Directory.GetFiles(directoryPath, "regime-run-*.json"));
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }

    private static RegimeRunDocument CreateDocument()
    {
        return new RegimeRunDocument(
            new DateOnly(2026, 7, 1),
            "CRS Rule-Based Engine",
            "0.1",
            "CRS Baseline",
            "0.1",
            "Goldilocks",
            "Goldilocks",
            0.7m,
            0.65m,
            "Confirmed",
            new[]
            {
                new RegimeRunProbability("Goldilocks", 0.7m, 1),
                new RegimeRunProbability("Reflation", 0.3m, 2)
            },
            new[]
            {
                new RegimeRunFeatureScore(
                    "GROWTH_MOM",
                    "Growth momentum",
                    "Growth",
                    1m,
                    55m,
                    0.8m,
                    null,
                    null,
                    "Growth is constructive.")
            },
            new[]
            {
                new RegimeRunExplanation(
                    "Growth momentum is a driver",
                    "Fixture explanation",
                    0.3m,
                    "GROWTH_MOM",
                    "Driver")
            },
            Array.Empty<string>(),
            new RegimeRunDataSource("Imported", "Data snapshot imported from local JSON file.", "memory://data.json"),
            new RegimeRunAllocation(
                "PartialRebalance",
                0.05m,
                0.00005m,
                new[]
                {
                    new RegimeRunAllocationLine("Cash", 0.05m, 0.05m, 0.05m, 0.02m, 0.20m, 0m, 0m),
                    new RegimeRunAllocationLine("GlobalEquity", 0.60m, 0.60m, 0.65m, 0.45m, 0.75m, 0.05m, 0.05m),
                    new RegimeRunAllocationLine("GovernmentBonds", 0.25m, 0.25m, 0.20m, 0.10m, 0.40m, -0.05m, -0.05m),
                    new RegimeRunAllocationLine("Gold", 0.10m, 0.10m, 0.10m, 0.00m, 0.20m, 0m, 0m)
                },
                new[] { "Constructive growth supports equity tilt." },
                Array.Empty<string>()));
    }
}
