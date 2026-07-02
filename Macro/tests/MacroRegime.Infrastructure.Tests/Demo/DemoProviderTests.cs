using MacroRegime.Application.Allocations;
using MacroRegime.Application.Analysis;
using MacroRegime.Application.Regimes;
using MacroRegime.Application.Reports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.Demo;
using MacroRegime.Infrastructure.Persistence;
using MacroRegime.Infrastructure.Reporting;
using MacroRegime.Reporting.Markdown;

namespace MacroRegime.Infrastructure.Tests.Demo;

public sealed class DemoProviderTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeDemoProviderTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task DemoProviders_ReturnDeterministicInputs()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));

        var dataSnapshot = await new DemoDataSnapshotProvider().GetSnapshotAsync(asOfDate);
        var modelVersion = await new DemoModelVersionProvider().GetActiveModelVersionAsync(asOfDate);
        var featureSetVersion = await new DemoFeatureSetProvider().GetActiveFeatureSetAsync(asOfDate);
        var policy = await new DemoStrategicAllocationPolicyProvider().GetPolicyAsync(asOfDate);
        var portfolio = await new DemoCurrentPortfolioProvider().GetCurrentPortfolioAsync(asOfDate);
        var tiltRules = await new DemoRegimeTiltRuleProvider().GetTiltRulesAsync(asOfDate);

        Assert.NotNull(dataSnapshot);
        Assert.Equal(asOfDate.Value, dataSnapshot.AsOfDate.Value);
        Assert.Equal(6, dataSnapshot.MacroObservations.Count);
        Assert.NotNull(modelVersion);
        Assert.Equal("0.1-demo", modelVersion.Version);
        Assert.NotNull(featureSetVersion);
        Assert.Equal(5, featureSetVersion.FeatureDefinitions.Count);
        Assert.NotNull(policy);
        Assert.Equal(4, policy.Bands.Count);
        Assert.NotNull(portfolio);
        Assert.Equal(4, portfolio.Weights.Count);
        Assert.Contains(tiltRules, rule => rule.Regime == RegimeType.Goldilocks && rule.AssetClass == AssetClass.GlobalEquity);
    }

    [Fact]
    public async Task DemoProviders_FeedFullLocalAnalysisPipeline()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var runStore = new JsonRegimeRunStore(Path.Combine(directoryPath, "runs"));
        var reportStore = new FileRegimeReportStore(Path.Combine(directoryPath, "reports"));
        var useCase = new RunRegimeAnalysisUseCase(
            new CalculateRegimeUseCase(
                new DemoDataSnapshotProvider(),
                new DemoModelVersionProvider(),
                new DemoFeatureSetProvider(),
                new BaselineRegimeDetector(),
                runStore),
            new GenerateAllocationProposalUseCase(
                new DemoStrategicAllocationPolicyProvider(),
                new DemoCurrentPortfolioProvider(),
                new DemoRegimeTiltRuleProvider(),
                new AllocationProposalService()),
            new GenerateRegimeReportUseCase(new MarkdownRegimeReportRenderer(), reportStore));

        var result = await useCase.ExecuteAsync(new RunRegimeAnalysisCommand(asOfDate));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Snapshot);
        Assert.NotNull(result.AllocationProposal);
        Assert.Equal(RegimeType.Goldilocks, result.Snapshot.PrimaryRegime);
        Assert.Equal(DecisionSuggestion.PartialRebalance, result.AllocationProposal.Suggestion);
        Assert.True(File.Exists(runStore.GetPath(asOfDate)));
        Assert.True(File.Exists(result.ReportLocation));
        Assert.Contains("Constructive growth supports equity tilt.", result.Markdown);
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }
}
