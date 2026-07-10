using System.Text.Json;
using MacroRegime.Application.Import;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Infrastructure.Tests.Import;

public sealed class JsonImportValidationServiceTests : IDisposable
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeImportValidationTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task ValidateAsync_ReturnsOkItems_ForValidLocalInputs()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var paths = await WriteValidFilesAsync(asOfDate);
        var service = new JsonImportValidationService();

        var report = await service.ValidateAsync(CreateCommand(asOfDate, paths, strictData: true, strictConfig: true));

        Assert.True(report.IsSuccess);
        Assert.Equal(6, report.Items.Count);
        Assert.Equal(6, report.OkCount);
        Assert.Equal(0, report.WarningCount);
        Assert.Equal(0, report.ErrorCount);
        Assert.All(report.Items, item => Assert.Equal(ImportValidationSeverity.Ok, item.Severity));
    }

    [Fact]
    public async Task ValidateAsync_ReturnsWarning_WhenOptionalDataFileIsMissingInNonStrictMode()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var paths = await WriteValidFilesAsync(asOfDate);
        var missingDataPath = Path.Combine(directoryPath, "missing-data.json");
        var service = new JsonImportValidationService();

        var report = await service.ValidateAsync(
            CreateCommand(asOfDate, paths with { DataFilePath = missingDataPath }, strictData: false, strictConfig: true));

        Assert.True(report.IsSuccess);
        Assert.Equal(1, report.WarningCount);
        var item = Assert.Single(report.Items, item => item.InputKind == "Macro data");
        Assert.Equal(ImportValidationSeverity.Warning, item.Severity);
        Assert.Contains("demo fallback", item.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ValidateAsync_ReturnsError_WhenDataFileIsMissingInStrictMode()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var paths = await WriteValidFilesAsync(asOfDate);
        var missingDataPath = Path.Combine(directoryPath, "missing-data.json");
        var service = new JsonImportValidationService();

        var report = await service.ValidateAsync(
            CreateCommand(asOfDate, paths with { DataFilePath = missingDataPath }, strictData: true, strictConfig: true));

        Assert.False(report.IsSuccess);
        Assert.Equal(1, report.ErrorCount);
        var item = Assert.Single(report.Items, item => item.InputKind == "Macro data");
        Assert.Equal(ImportValidationSeverity.Error, item.Severity);
        Assert.Contains("does not exist", item.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ValidateAsync_ReturnsError_WhenPortfolioAsOfDateDoesNotMatchInStrictMode()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var paths = await WriteValidFilesAsync(asOfDate);
        var portfolioPath = await WriteJsonAsync(
            "portfolio-mismatch.json",
            CreatePortfolioRecord(new DateOnly(2026, 6, 1)));
        var service = new JsonImportValidationService();

        var report = await service.ValidateAsync(
            CreateCommand(asOfDate, paths with { PortfolioFilePath = portfolioPath }, strictData: true, strictConfig: true));

        Assert.False(report.IsSuccess);
        var item = Assert.Single(report.Items, item => item.InputKind == "Current portfolio");
        Assert.Equal(ImportValidationSeverity.Error, item.Severity);
        Assert.Contains("expected 2026-07-01", item.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task Render_ProducesReadableMarkdownSummary()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var paths = await WriteValidFilesAsync(asOfDate);
        var report = await new JsonImportValidationService()
            .ValidateAsync(CreateCommand(asOfDate, paths, strictData: true, strictConfig: true));

        var markdown = ImportValidationMarkdownRenderer.Render(report);

        Assert.Contains("# Import Validation Report", markdown);
        Assert.Contains("As-of date: 2026-07-01", markdown);
        Assert.Contains("OK: 6", markdown);
        Assert.Contains("Macro data", markdown);
        Assert.Contains("Current portfolio", markdown);
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }

    private static ValidateImportCommand CreateCommand(
        DateOnly asOfDate,
        ImportValidationPaths paths,
        bool strictData,
        bool strictConfig)
    {
        return new ValidateImportCommand(
            asOfDate,
            paths.DataFilePath,
            paths.ModelFilePath,
            paths.FeatureSetFilePath,
            paths.PolicyFilePath,
            paths.PortfolioFilePath,
            paths.TiltsFilePath,
            strictData,
            strictConfig);
    }

    private async Task<ImportValidationPaths> WriteValidFilesAsync(DateOnly asOfDate)
    {
        return new ImportValidationPaths(
            await WriteJsonAsync("macro-data.json", CreateDataSnapshotRecord(asOfDate)),
            await WriteJsonAsync("model.json", CreateModelVersionRecord()),
            await WriteJsonAsync("feature-set.json", CreateFeatureSetVersionRecord()),
            await WriteJsonAsync("policy.json", CreatePolicyRecord()),
            await WriteJsonAsync("portfolio.json", CreatePortfolioRecord(asOfDate)),
            await WriteJsonAsync("tilts.json", CreateTiltRulesRecord()));
    }

    private async Task<string> WriteJsonAsync<TRecord>(string fileName, TRecord record)
    {
        Directory.CreateDirectory(directoryPath);
        var path = Path.Combine(directoryPath, fileName);
        await File.WriteAllTextAsync(path, JsonSerializer.Serialize(record, SerializerOptions));
        return path;
    }

    private static JsonDataSnapshotRecord CreateDataSnapshotRecord(DateOnly asOfDate)
    {
        return new JsonDataSnapshotRecord(
            JsonDataSnapshotRecordMapper.CurrentSchemaVersion,
            asOfDate,
            new[]
            {
                new JsonMacroObservationRecord("INDPRO_YOY", "Industrial production YoY", "Growth", new DateOnly(2026, 6, 30), asOfDate, asOfDate, 5m, "Fixture", "Percent change")
            },
            Array.Empty<JsonMarketObservationRecord>());
    }

    private static JsonModelVersionRecord CreateModelVersionRecord()
    {
        return new JsonModelVersionRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            "CRS Rule-Based Engine",
            "0.1-local",
            "Baseline",
            new Dictionary<string, decimal> { ["confirmation_threshold"] = 0.55m },
            new DateOnly(2026, 1, 1),
            "Fixture model.");
    }

    private static JsonFeatureSetVersionRecord CreateFeatureSetVersionRecord()
    {
        return new JsonFeatureSetVersionRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            "CRS Baseline",
            "0.1-local",
            new[]
            {
                new JsonFeatureDefinitionRecord("GROWTH_MOM", "Growth momentum", "Growth", "Fixture", 1m, "HigherIsRiskOn", 6, true)
            });
    }

    private static JsonStrategicAllocationPolicyRecord CreatePolicyRecord()
    {
        return new JsonStrategicAllocationPolicyRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            "Balanced",
            new[]
            {
                new JsonAllocationBandRecord("Cash", 0.02m, 0.05m, 0.20m),
                new JsonAllocationBandRecord("GlobalEquity", 0.45m, 0.60m, 0.75m),
                new JsonAllocationBandRecord("GovernmentBonds", 0.10m, 0.25m, 0.40m),
                new JsonAllocationBandRecord("Gold", 0.00m, 0.10m, 0.20m)
            },
            0.20m,
            0.01m);
    }

    private static JsonCurrentPortfolioRecord CreatePortfolioRecord(DateOnly asOfDate)
    {
        return new JsonCurrentPortfolioRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            asOfDate,
            new[]
            {
                new JsonPortfolioWeightRecord("Cash", 0.05m),
                new JsonPortfolioWeightRecord("GlobalEquity", 0.60m),
                new JsonPortfolioWeightRecord("GovernmentBonds", 0.25m),
                new JsonPortfolioWeightRecord("Gold", 0.10m)
            });
    }

    private static JsonRegimeTiltRulesRecord CreateTiltRulesRecord()
    {
        return new JsonRegimeTiltRulesRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            new[]
            {
                new JsonRegimeTiltRuleRecord("Goldilocks", "GlobalEquity", 0.05m, "Constructive growth supports equity tilt.")
            });
    }

    private sealed record ImportValidationPaths(
        string DataFilePath,
        string ModelFilePath,
        string FeatureSetFilePath,
        string PolicyFilePath,
        string PortfolioFilePath,
        string TiltsFilePath);
}
