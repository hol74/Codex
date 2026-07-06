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

public sealed class JsonConfigurationProviderTests : IDisposable
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeConfigurationTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task Providers_ReadVersionedConfigurationFiles()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var modelPath = await WriteRecordAsync("model.json", CreateModelVersionRecord());
        var featureSetPath = await WriteRecordAsync("feature-set.json", CreateFeatureSetVersionRecord());
        var policyPath = await WriteRecordAsync("policy.json", CreatePolicyRecord());
        var portfolioPath = await WriteRecordAsync("portfolio.json", CreatePortfolioRecord(asOfDate.Value));
        var tiltsPath = await WriteRecordAsync("tilts.json", CreateTiltRulesRecord());

        var model = await new JsonModelVersionProvider(modelPath).GetActiveModelVersionAsync(asOfDate);
        var featureSet = await new JsonFeatureSetProvider(featureSetPath).GetActiveFeatureSetAsync(asOfDate);
        var policy = await new JsonStrategicAllocationPolicyProvider(policyPath).GetPolicyAsync(asOfDate);
        var portfolio = await new JsonCurrentPortfolioProvider(portfolioPath).GetCurrentPortfolioAsync(asOfDate);
        var tilts = await new JsonRegimeTiltRuleProvider(tiltsPath).GetTiltRulesAsync(asOfDate);

        Assert.NotNull(model);
        Assert.NotNull(featureSet);
        Assert.NotNull(policy);
        Assert.Equal("0.1-test", model.Version);
        Assert.Equal(5, featureSet.FeatureDefinitions.Count);
        Assert.Equal(4, policy.Bands.Count);
        Assert.NotNull(portfolio);
        Assert.Equal(0.60m, portfolio.WeightOf(AssetClass.GlobalEquity));
        Assert.Contains(tilts, tilt => tilt.Regime == RegimeType.Goldilocks && tilt.AssetClass == AssetClass.GlobalEquity);
    }

    [Fact]
    public async Task Provider_Throws_WhenSchemaVersionIsUnsupported()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var path = await WriteRecordAsync("model.json", CreateModelVersionRecord() with { SchemaVersion = 999 });
        var provider = new JsonModelVersionProvider(path);

        var exception = await Assert.ThrowsAsync<InvalidDataException>(() => provider.GetActiveModelVersionAsync(asOfDate));

        Assert.Contains("Unsupported model version schema version", exception.Message);
    }

    [Fact]
    public async Task CurrentPortfolioProvider_UsesFallback_WhenAsOfDateDoesNotMatch()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var path = await WriteRecordAsync("portfolio.json", CreatePortfolioRecord(new DateOnly(2026, 6, 30)));
        var provider = new JsonCurrentPortfolioProvider(path, new DemoCurrentPortfolioProvider());

        var portfolio = await provider.GetCurrentPortfolioAsync(asOfDate);

        Assert.NotNull(portfolio);
        Assert.Equal(0.60m, portfolio.WeightOf(AssetClass.GlobalEquity));
    }

    [Fact]
    public async Task CurrentPortfolioProvider_Throws_WhenStrictAndAsOfDateDoesNotMatch()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var path = await WriteRecordAsync("portfolio.json", CreatePortfolioRecord(new DateOnly(2026, 6, 30)));
        var provider = new JsonCurrentPortfolioProvider(path, new DemoCurrentPortfolioProvider(), strict: true);

        var exception = await Assert.ThrowsAsync<InvalidDataException>(() => provider.GetCurrentPortfolioAsync(asOfDate));

        Assert.Contains("expected 2026-07-01", exception.Message);
    }

    [Fact]
    public async Task LocalJsonConfiguration_FeedsFullAnalysisPipeline()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var dataPath = await WriteRecordAsync("macro-data.json", CreateDataSnapshotRecord(asOfDate));
        var modelPath = await WriteRecordAsync("model.json", CreateModelVersionRecord());
        var featureSetPath = await WriteRecordAsync("feature-set.json", CreateFeatureSetVersionRecord());
        var policyPath = await WriteRecordAsync("policy.json", CreatePolicyRecord());
        var portfolioPath = await WriteRecordAsync("portfolio.json", CreatePortfolioRecord(asOfDate));
        var tiltsPath = await WriteRecordAsync("tilts.json", CreateTiltRulesRecord());
        var runStore = new JsonRegimeRunStore(Path.Combine(directoryPath, "runs"));
        var reportStore = new FileRegimeReportStore(Path.Combine(directoryPath, "reports"));
        var useCase = new RunRegimeAnalysisUseCase(
            new CalculateRegimeUseCase(
                new JsonDataSnapshotProvider(dataPath, strict: true),
                new JsonModelVersionProvider(modelPath, strict: true),
                new JsonFeatureSetProvider(featureSetPath, strict: true),
                new BaselineRegimeDetector(),
                runStore),
            new GenerateAllocationProposalUseCase(
                new JsonStrategicAllocationPolicyProvider(policyPath, strict: true),
                new JsonCurrentPortfolioProvider(portfolioPath, strict: true),
                new JsonRegimeTiltRuleProvider(tiltsPath, strict: true),
                new AllocationProposalService()),
            new GenerateRegimeReportUseCase(new MarkdownRegimeReportRenderer(), reportStore));

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

    private async Task<string> WriteRecordAsync<TRecord>(string fileName, TRecord record)
    {
        Directory.CreateDirectory(directoryPath);
        var filePath = Path.Combine(directoryPath, fileName);
        var json = JsonSerializer.Serialize(record, SerializerOptions);
        await File.WriteAllTextAsync(filePath, json);
        return filePath;
    }

    private static JsonModelVersionRecord CreateModelVersionRecord()
    {
        return new JsonModelVersionRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            "CRS Rule-Based Engine",
            "0.1-test",
            "Baseline",
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m
            },
            new DateOnly(2026, 7, 1),
            "Test model.");
    }

    private static JsonFeatureSetVersionRecord CreateFeatureSetVersionRecord()
    {
        return new JsonFeatureSetVersionRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            "CRS Baseline",
            "0.1-test",
            new[]
            {
                Feature("GROWTH_MOM", "Growth momentum", EconomicDimension.Growth, "HigherIsRiskOn"),
                Feature("INFL_PRESS", "Inflation pressure", EconomicDimension.Inflation, "HigherIsRiskOff"),
                Feature("RISK_APPETITE", "Risk appetite", EconomicDimension.Risk, "HigherIsRiskOn"),
                Feature("MONETARY_COND", "Monetary conditions", EconomicDimension.Monetary, "HigherIsRiskOn"),
                Feature("CREDIT_STRESS", "Credit stress", EconomicDimension.Credit, "HigherIsRiskOff")
            });
    }

    private static JsonFeatureDefinitionRecord Feature(string code, string name, EconomicDimension dimension, string polarity)
    {
        return new JsonFeatureDefinitionRecord(
            code,
            name,
            dimension.ToString(),
            "Test feature.",
            1m,
            polarity,
            6,
            true);
    }

    private static JsonStrategicAllocationPolicyRecord CreatePolicyRecord()
    {
        return new JsonStrategicAllocationPolicyRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            "Balanced Test IPS",
            new[]
            {
                Band(AssetClass.Cash, 0.02m, 0.05m, 0.20m),
                Band(AssetClass.GlobalEquity, 0.45m, 0.60m, 0.75m),
                Band(AssetClass.GovernmentBonds, 0.10m, 0.25m, 0.40m),
                Band(AssetClass.Gold, 0.00m, 0.10m, 0.20m)
            },
            0.25m,
            0.001m);
    }

    private static JsonAllocationBandRecord Band(AssetClass assetClass, decimal minimum, decimal strategic, decimal maximum)
    {
        return new JsonAllocationBandRecord(assetClass.ToString(), minimum, strategic, maximum);
    }

    private static JsonCurrentPortfolioRecord CreatePortfolioRecord(DateOnly asOfDate)
    {
        return new JsonCurrentPortfolioRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            asOfDate,
            new[]
            {
                Weight(AssetClass.Cash, 0.05m),
                Weight(AssetClass.GlobalEquity, 0.60m),
                Weight(AssetClass.GovernmentBonds, 0.25m),
                Weight(AssetClass.Gold, 0.10m)
            });
    }

    private static JsonPortfolioWeightRecord Weight(AssetClass assetClass, decimal weight)
    {
        return new JsonPortfolioWeightRecord(assetClass.ToString(), weight);
    }

    private static JsonRegimeTiltRulesRecord CreateTiltRulesRecord()
    {
        return new JsonRegimeTiltRulesRecord(
            JsonConfigurationRecordMapper.CurrentSchemaVersion,
            new[]
            {
                Tilt(RegimeType.Goldilocks, AssetClass.GlobalEquity, 0.08m),
                Tilt(RegimeType.Goldilocks, AssetClass.GovernmentBonds, -0.05m),
                Tilt(RegimeType.Goldilocks, AssetClass.Cash, -0.03m),
                Tilt(RegimeType.RecessionStress, AssetClass.GlobalEquity, -0.10m)
            });
    }

    private static JsonRegimeTiltRuleRecord Tilt(RegimeType regime, AssetClass assetClass, decimal tilt)
    {
        return new JsonRegimeTiltRuleRecord(regime.ToString(), assetClass.ToString(), tilt, "Test tilt.");
    }

    private static JsonDataSnapshotRecord CreateDataSnapshotRecord(DateOnly asOfDate)
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
