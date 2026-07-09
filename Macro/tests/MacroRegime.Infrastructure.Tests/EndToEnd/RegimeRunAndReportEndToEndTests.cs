using MacroRegime.Application.Allocations;
using MacroRegime.Application.Analysis;
using MacroRegime.Application.Regimes;
using MacroRegime.Application.Reports;
using MacroRegime.Application.Runs;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Explanations;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.Demo;
using MacroRegime.Infrastructure.Persistence;
using MacroRegime.Infrastructure.Reporting;
using MacroRegime.Reporting.Markdown;

namespace MacroRegime.Infrastructure.Tests.EndToEnd;

public sealed class RegimeRunAndReportEndToEndTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeEndToEndTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task SaveRunAndGenerateReport_UsesOnlyLocalFileAdapters()
    {
        var snapshot = CreateSnapshot();
        var allocationProposal = CreateAllocationProposal();
        var runStore = new JsonRegimeRunStore(Path.Combine(directoryPath, "runs"));
        var reportStore = new FileRegimeReportStore(Path.Combine(directoryPath, "reports"));
        var reportUseCase = new GenerateRegimeReportUseCase(new MarkdownRegimeReportRenderer(), reportStore);

        await runStore.SaveAsync(RegimeRunDocument.FromDomain(snapshot, allocationProposal));
        var reportResult = await reportUseCase.ExecuteAsync(new GenerateRegimeReportCommand(snapshot, allocationProposal));

        var runPath = runStore.GetPath(snapshot.AsOfDate.Value);
        Assert.True(File.Exists(runPath));
        Assert.True(File.Exists(reportResult.Location));
        Assert.Equal(reportStore.GetPath(snapshot.AsOfDate.Value), reportResult.Location);

        var report = await File.ReadAllTextAsync(reportResult.Location);
        Assert.Contains("# Macro-Regime Report", report);
        Assert.Contains("Primary regime: Goldilocks", report);
        Assert.Contains("## Allocation Proposal", report);
        Assert.Contains("Decision suggestion: PartialRebalance", report);
    }

    [Fact]
    public async Task RunRegimeAnalysis_UsesOnlyLocalFileAdapters()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var runStore = new JsonRegimeRunStore(Path.Combine(directoryPath, "analysis-runs"));
        var reportStore = new FileRegimeReportStore(Path.Combine(directoryPath, "analysis-reports"));
        var useCase = new RunRegimeAnalysisUseCase(
            new CalculateRegimeUseCase(
                new DemoDataSnapshotProvider(),
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
        Assert.NotNull(result.AllocationProposal);
        Assert.Equal(RegimeType.Goldilocks, result.Snapshot.PrimaryRegime);
        Assert.Equal(DecisionSuggestion.PartialRebalance, result.AllocationProposal.Suggestion);
        Assert.True(File.Exists(runStore.GetPath(asOfDate)));
        Assert.True(File.Exists(result.ReportLocation));

        var storedRun = await runStore.LoadAsync(asOfDate);
        Assert.NotNull(storedRun);
        Assert.Equal("Goldilocks", storedRun.PrimaryRegime);
        Assert.NotNull(storedRun.Allocation);
        Assert.Equal("PartialRebalance", storedRun.Allocation.Suggestion);
        Assert.NotNull(storedRun.DataSource);
        Assert.Equal("Demo", storedRun.DataSource.Kind);

        var report = await File.ReadAllTextAsync(result.ReportLocation!);
        Assert.Contains("# Macro-Regime Report", report);
        Assert.Contains("Primary regime: Goldilocks", report);
        Assert.Contains("## Allocation Proposal", report);
        Assert.Contains("Constructive growth supports equity tilt.", report);
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }

    private static RegimeSnapshot CreateSnapshot()
    {
        return new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            CreateModelVersion(),
            new FeatureSetVersion("CRS Baseline", "0.1", new[] { Feature("GROWTH_MOM", "Growth momentum", EconomicDimension.Growth, FeaturePolarity.HigherIsRiskOn) }),
            RegimeType.Goldilocks,
            new RegimeConfidence(0.7m),
            new NormalizedScore(0.65m),
            "Confirmed",
            new[]
            {
                new RegimeProbability(RegimeType.Goldilocks, new Probability(0.7m), 1),
                new RegimeProbability(RegimeType.Reflation, new Probability(0.3m), 2)
            },
            new[]
            {
                new FeatureScore(
                    "GROWTH_MOM",
                    "Growth momentum",
                    EconomicDimension.Growth,
                    new FeatureWeight(1m),
                    55m,
                    new NormalizedScore(0.8m),
                    null,
                    null,
                    "Growth is constructive.")
            },
            new[]
            {
                new RegimeExplanation(
                    "Growth momentum is a driver",
                    "Fixture explanation",
                    0.3m,
                    "GROWTH_MOM",
                    RegimeExplanationKind.Driver)
            },
            Array.Empty<string>());
    }

    private static FeatureDefinition Feature(string code, string name, EconomicDimension dimension, FeaturePolarity polarity)
    {
        return new FeatureDefinition(
            code,
            name,
            dimension,
            "Baseline v0.1 formula",
            new FeatureWeight(1m),
            polarity,
            6,
            true);
    }

    private static ModelVersion CreateModelVersion()
    {
        return new ModelVersion(
            "CRS Rule-Based Engine",
            "0.1",
            ModelRole.Baseline,
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m
            },
            new DateOnly(2026, 7, 1),
            "Baseline model");
    }

    private static AllocationProposal CreateAllocationProposal()
    {
        return new AllocationProposal(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            RegimeType.Goldilocks,
            DecisionSuggestion.PartialRebalance,
            new AllocationWeight(0.05m),
            0.00005m,
            new[]
            {
                new AllocationProposalLine(
                    AssetClass.Cash,
                    new AllocationWeight(0.05m),
                    new AllocationWeight(0.05m),
                    new AllocationWeight(0.05m),
                    new AllocationWeight(0.02m),
                    new AllocationWeight(0.20m),
                    0m,
                    0m),
                new AllocationProposalLine(
                    AssetClass.GlobalEquity,
                    new AllocationWeight(0.60m),
                    new AllocationWeight(0.60m),
                    new AllocationWeight(0.65m),
                    new AllocationWeight(0.45m),
                    new AllocationWeight(0.75m),
                    0.05m,
                    0.05m),
                new AllocationProposalLine(
                    AssetClass.GovernmentBonds,
                    new AllocationWeight(0.25m),
                    new AllocationWeight(0.25m),
                    new AllocationWeight(0.20m),
                    new AllocationWeight(0.10m),
                    new AllocationWeight(0.40m),
                    -0.05m,
                    -0.05m),
                new AllocationProposalLine(
                    AssetClass.Gold,
                    new AllocationWeight(0.10m),
                    new AllocationWeight(0.10m),
                    new AllocationWeight(0.10m),
                    new AllocationWeight(0.00m),
                    new AllocationWeight(0.20m),
                    0m,
                    0m)
            },
            new[] { "Constructive growth supports equity tilt." },
            Array.Empty<string>());
    }
}
