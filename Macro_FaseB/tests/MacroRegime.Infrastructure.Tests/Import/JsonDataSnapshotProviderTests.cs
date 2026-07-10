using System.Text.Json;
using MacroRegime.Application.Allocations;
using MacroRegime.Application.Analysis;
using MacroRegime.Application.Regimes;
using MacroRegime.Application.Reports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.Demo;
using MacroRegime.Infrastructure.Import;
using MacroRegime.Infrastructure.Persistence;
using MacroRegime.Infrastructure.Reporting;
using MacroRegime.Reporting.Markdown;

namespace MacroRegime.Infrastructure.Tests.Import;

public sealed class JsonDataSnapshotProviderTests : IDisposable
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeImportTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task GetSnapshotAsync_ReadsVersionedImportFile()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var filePath = Path.Combine(directoryPath, "macro-data.json");
        await WriteRecordAsync(filePath, CreateGoldilocksImportRecord(asOfDate.Value));
        var provider = new JsonDataSnapshotProvider(filePath);

        var snapshot = await provider.GetSnapshotAsync(asOfDate);

        Assert.NotNull(snapshot);
        Assert.Equal(asOfDate.Value, snapshot.AsOfDate.Value);
        Assert.True(snapshot.TryGetValue("ISM_PMI", out var pmi));
        Assert.Equal(55m, pmi);
        Assert.Equal(6, snapshot.MacroObservations.Count);
        Assert.Empty(snapshot.MarketObservations);
        Assert.Equal(DataSnapshotSourceKind.Imported, provider.LastSourceInfo.Kind);
    }

    [Fact]
    public async Task GetSnapshotAsync_Throws_WhenSchemaVersionIsUnsupported()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var filePath = Path.Combine(directoryPath, "macro-data.json");
        var record = CreateGoldilocksImportRecord(asOfDate.Value) with { SchemaVersion = 999 };
        await WriteRecordAsync(filePath, record);
        var provider = new JsonDataSnapshotProvider(filePath, new DemoDataSnapshotProvider());

        var exception = await Assert.ThrowsAsync<InvalidDataException>(() => provider.GetSnapshotAsync(asOfDate));

        Assert.Contains("Unsupported data snapshot schema version", exception.Message);
    }

    [Fact]
    public async Task GetSnapshotAsync_Throws_WhenRequiredFieldIsMissing()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var filePath = Path.Combine(directoryPath, "macro-data.json");
        var record = CreateGoldilocksImportRecord(asOfDate.Value) with
        {
            MacroObservations = new[]
            {
                new JsonMacroObservationRecord(
                    string.Empty,
                    "ISM manufacturing PMI",
                    EconomicDimension.Growth.ToString(),
                    new DateOnly(2026, 6, 30),
                    asOfDate.Value,
                    asOfDate.Value,
                    55m,
                    "Fixture",
                    "Index")
            }
        };
        await WriteRecordAsync(filePath, record);
        var provider = new JsonDataSnapshotProvider(filePath);

        var exception = await Assert.ThrowsAsync<InvalidDataException>(() => provider.GetSnapshotAsync(asOfDate));

        Assert.Contains("Macro series code is required", exception.Message);
    }

    [Fact]
    public async Task GetSnapshotAsync_UsesFallback_WhenFileIsMissing()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var filePath = Path.Combine(directoryPath, "missing.json");
        var provider = new JsonDataSnapshotProvider(filePath, new DemoDataSnapshotProvider());

        var snapshot = await provider.GetSnapshotAsync(asOfDate);

        Assert.NotNull(snapshot);
        Assert.Equal(asOfDate.Value, snapshot.AsOfDate.Value);
        Assert.Equal(6, snapshot.MacroObservations.Count);
        Assert.Equal(DataSnapshotSourceKind.DemoFallback, provider.LastSourceInfo.Kind);
    }

    [Fact]
    public async Task GetSnapshotAsync_UsesFallback_WhenImportAsOfDateDoesNotMatch()
    {
        var requestedAsOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var filePath = Path.Combine(directoryPath, "macro-data.json");
        await WriteRecordAsync(filePath, CreateGoldilocksImportRecord(new DateOnly(2026, 6, 30)));
        var provider = new JsonDataSnapshotProvider(filePath, new DemoDataSnapshotProvider());

        var snapshot = await provider.GetSnapshotAsync(requestedAsOfDate);

        Assert.NotNull(snapshot);
        Assert.Equal(requestedAsOfDate.Value, snapshot.AsOfDate.Value);
        Assert.Equal(6, snapshot.MacroObservations.Count);
        Assert.Equal(DataSnapshotSourceKind.DemoFallback, provider.LastSourceInfo.Kind);
    }

    [Fact]
    public async Task GetSnapshotAsync_Throws_WhenStrictAndImportAsOfDateDoesNotMatch()
    {
        var requestedAsOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var filePath = Path.Combine(directoryPath, "macro-data.json");
        await WriteRecordAsync(filePath, CreateGoldilocksImportRecord(new DateOnly(2026, 6, 30)));
        var provider = new JsonDataSnapshotProvider(filePath, new DemoDataSnapshotProvider(), strict: true);

        var exception = await Assert.ThrowsAsync<InvalidDataException>(() => provider.GetSnapshotAsync(requestedAsOfDate));

        Assert.Contains("expected 2026-07-01", exception.Message);
    }

    [Fact]
    public async Task ImportedSnapshot_FeedsFullLocalAnalysisPipeline()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var filePath = Path.Combine(directoryPath, "macro-data.json");
        await WriteRecordAsync(filePath, CreateGoldilocksImportRecord(asOfDate));
        var runStore = new JsonRegimeRunStore(Path.Combine(directoryPath, "runs"));
        var reportStore = new FileRegimeReportStore(Path.Combine(directoryPath, "reports"));
        var useCase = new RunRegimeAnalysisUseCase(
            new CalculateRegimeUseCase(
                new JsonDataSnapshotProvider(filePath, new DemoDataSnapshotProvider()),
                new DemoModelVersionProvider(),
                new DemoFeatureSetProvider(),
                new BaselineRegimeDetector()),
            new GenerateAllocationProposalUseCase(
                new DemoStrategicAllocationPolicyProvider(),
                new DemoCurrentPortfolioProvider(),
                new DemoRegimeTiltRuleProvider(),
                new AllocationProposalService()),
            new GenerateRegimeReportUseCase(new MarkdownRegimeReportRenderer(), reportStore),
            runStore);

        var result = await useCase.ExecuteAsync(new RunRegimeAnalysisCommand(asOfDate));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Snapshot);
        Assert.Equal(RegimeType.Goldilocks, result.Snapshot.PrimaryRegime);
        Assert.NotNull(result.AllocationProposal);
        Assert.Equal(DecisionSuggestion.PartialRebalance, result.AllocationProposal.Suggestion);
        Assert.True(File.Exists(runStore.GetPath(asOfDate)));
        Assert.True(File.Exists(result.ReportLocation));
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }

    private static async Task WriteRecordAsync(string filePath, JsonDataSnapshotRecord record)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(filePath)!);
        var json = JsonSerializer.Serialize(record, SerializerOptions);
        await File.WriteAllTextAsync(filePath, json);
    }

    private static JsonDataSnapshotRecord CreateGoldilocksImportRecord(DateOnly asOfDate)
    {
        var observationDate = new DateOnly(2026, 6, 30);

        return new JsonDataSnapshotRecord(
            JsonDataSnapshotRecordMapper.CurrentSchemaVersion,
            asOfDate,
            new[]
            {
                Macro("ISM_PMI", "ISM manufacturing PMI", EconomicDimension.Growth, 55m, observationDate, asOfDate),
                Macro("SAHM", "Sahm rule recession indicator", EconomicDimension.Growth, 0.05m, observationDate, asOfDate),
                Macro("T10YIE", "10-year breakeven inflation", EconomicDimension.Inflation, 2.0m, observationDate, asOfDate),
                Macro("VIX", "CBOE volatility index", EconomicDimension.Risk, 14m, observationDate, asOfDate),
                Macro("YC_10Y2Y", "10-year minus 2-year Treasury slope", EconomicDimension.Monetary, 0.5m, observationDate, asOfDate),
                Macro("HY_OAS", "High-yield option-adjusted spread", EconomicDimension.Credit, 300m, observationDate, asOfDate)
            },
            Array.Empty<JsonMarketObservationRecord>());
    }

    private static JsonMacroObservationRecord Macro(
        string code,
        string name,
        EconomicDimension dimension,
        decimal value,
        DateOnly observationDate,
        DateOnly publicationDate)
    {
        return new JsonMacroObservationRecord(
            code,
            name,
            dimension.ToString(),
            observationDate,
            publicationDate,
            publicationDate,
            value,
            "Fixture",
            "Index");
    }
}
