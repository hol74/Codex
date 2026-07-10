using MacroRegime.Application.Allocations;
using MacroRegime.Application.Analysis;
using MacroRegime.Application.Ports;
using MacroRegime.Application.Regimes;
using MacroRegime.Application.Reports;
using MacroRegime.Application.Runs;
using MacroRegime.Application.Tests.Allocations;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Tests.Analysis;

public sealed class RunRegimeAnalysisUseCaseTests
{
    [Fact]
    public async Task ExecuteAsync_RunsRegimeAllocationAndReportPipeline()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var reportStore = new FakeReportStore("memory://macro-regime-report.md");
        var useCase = CreateUseCase(
            new FakeModelVersionProvider(CreateModelVersion()),
            new FakeFeatureSetProvider(CreateFeatureSetVersion()),
            new FakePolicyProvider(AllocationProposalTestFixtures.CreatePolicy()),
            new FakePortfolioProvider(AllocationProposalTestFixtures.CreatePortfolio()),
            reportStore);

        var result = await useCase.ExecuteAsync(new RunRegimeAnalysisCommand(asOfDate));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Snapshot);
        Assert.NotNull(result.AllocationProposal);
        Assert.Equal(RegimeType.Goldilocks, result.Snapshot.PrimaryRegime);
        Assert.Equal(DecisionSuggestion.PartialRebalance, result.AllocationProposal.Suggestion);
        Assert.Equal("memory://macro-regime-report.md", result.ReportLocation);
        Assert.Contains("## Allocation Proposal", result.Markdown);
        Assert.Contains("Decision suggestion: PartialRebalance", reportStore.Markdown);
    }

    [Fact]
    public async Task ExecuteAsync_UpsertsRunManifest_WhenManifestStoreIsProvided()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var manifestStore = new FakeManifestStore();
        var reportStore = new FakeReportStore("memory://macro-regime-report.md");
        var calculateRegime = new CalculateRegimeUseCase(
            new FakeDataSnapshotProvider(CreateGoldilocksDataSnapshot(new AsOfDate(asOfDate))),
            new FakeModelVersionProvider(CreateModelVersion()),
            new FakeFeatureSetProvider(CreateFeatureSetVersion()),
            new BaselineRegimeDetector());

        var useCase = new RunRegimeAnalysisUseCase(
            calculateRegime,
            new GenerateAllocationProposalUseCase(
                new FakePolicyProvider(AllocationProposalTestFixtures.CreatePolicy()),
                new FakePortfolioProvider(AllocationProposalTestFixtures.CreatePortfolio()),
                new FakeTiltRuleProvider(AllocationProposalTestFixtures.CreateTiltRules()),
                new AllocationProposalService()),
            new GenerateRegimeReportUseCase(new FakeReportRenderer(), reportStore),
            new FakeRegimeRunStore("memory://regime-run.json"),
            manifestStore);

        var result = await useCase.ExecuteAsync(new RunRegimeAnalysisCommand(asOfDate));

        Assert.True(result.IsSuccess);
        Assert.Equal("memory://regime-run.json", result.RunLocation);

        var entry = Assert.Single(manifestStore.Entries);
        Assert.Equal(asOfDate, entry.AsOfDate);
        Assert.Equal("memory://regime-run.json", entry.RunLocation);
        Assert.Equal("memory://macro-regime-report.md", entry.ReportLocation);
        Assert.Equal("Goldilocks", entry.PrimaryRegime);
        Assert.Equal("PartialRebalance", entry.AllocationSuggestion);
    }

    [Fact]
    public async Task ExecuteAsync_SavesRunDocumentWithAllocationAndDataSource_WhenRunStoreIsProvided()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var runStore = new FakeRegimeRunStore("memory://regime-run.json");
        var reportStore = new FakeReportStore("memory://macro-regime-report.md");
        var calculateRegime = new CalculateRegimeUseCase(
            new FakeDataSnapshotProvider(CreateGoldilocksDataSnapshot(new AsOfDate(asOfDate))),
            new FakeModelVersionProvider(CreateModelVersion()),
            new FakeFeatureSetProvider(CreateFeatureSetVersion()),
            new BaselineRegimeDetector());

        var useCase = new RunRegimeAnalysisUseCase(
            calculateRegime,
            new GenerateAllocationProposalUseCase(
                new FakePolicyProvider(AllocationProposalTestFixtures.CreatePolicy()),
                new FakePortfolioProvider(AllocationProposalTestFixtures.CreatePortfolio()),
                new FakeTiltRuleProvider(AllocationProposalTestFixtures.CreateTiltRules()),
                new AllocationProposalService()),
            new GenerateRegimeReportUseCase(new FakeReportRenderer(), reportStore),
            runStore);

        var result = await useCase.ExecuteAsync(new RunRegimeAnalysisCommand(asOfDate));

        Assert.True(result.IsSuccess);
        Assert.Equal("memory://regime-run.json", result.RunLocation);
        Assert.NotNull(runStore.SavedDocument);
        Assert.Equal(asOfDate, runStore.SavedDocument.AsOfDate);
        Assert.Equal("Goldilocks", runStore.SavedDocument.PrimaryRegime);
        Assert.NotNull(runStore.SavedDocument.Allocation);
        Assert.Equal("PartialRebalance", runStore.SavedDocument.Allocation.Suggestion);
        Assert.NotEmpty(runStore.SavedDocument.Allocation.Lines);
        Assert.NotNull(runStore.SavedDocument.DataSource);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsFailure_WhenRegimeCalculationFails()
    {
        var reportStore = new FakeReportStore("memory://macro-regime-report.md");
        var useCase = CreateUseCase(
            new FakeModelVersionProvider(null),
            new FakeFeatureSetProvider(CreateFeatureSetVersion()),
            new FakePolicyProvider(AllocationProposalTestFixtures.CreatePolicy()),
            new FakePortfolioProvider(AllocationProposalTestFixtures.CreatePortfolio()),
            reportStore);

        var result = await useCase.ExecuteAsync(new RunRegimeAnalysisCommand(new DateOnly(2026, 7, 1)));

        Assert.False(result.IsSuccess);
        Assert.Equal("Model version is missing.", result.Error);
        Assert.Null(reportStore.Markdown);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsFailure_WhenAllocationProposalFails()
    {
        var reportStore = new FakeReportStore("memory://macro-regime-report.md");
        var useCase = CreateUseCase(
            new FakeModelVersionProvider(CreateModelVersion()),
            new FakeFeatureSetProvider(CreateFeatureSetVersion()),
            new FakePolicyProvider(null),
            new FakePortfolioProvider(AllocationProposalTestFixtures.CreatePortfolio()),
            reportStore);

        var result = await useCase.ExecuteAsync(new RunRegimeAnalysisCommand(new DateOnly(2026, 7, 1)));

        Assert.False(result.IsSuccess);
        Assert.Equal("Strategic allocation policy is missing.", result.Error);
        Assert.Null(reportStore.Markdown);
    }

    private static RunRegimeAnalysisUseCase CreateUseCase(
        IModelVersionProvider modelVersionProvider,
        IFeatureSetProvider featureSetProvider,
        IStrategicAllocationPolicyProvider policyProvider,
        ICurrentPortfolioProvider portfolioProvider,
        IRegimeReportStore reportStore)
    {
        var calculateRegime = new CalculateRegimeUseCase(
            new FakeDataSnapshotProvider(CreateGoldilocksDataSnapshot(new AsOfDate(new DateOnly(2026, 7, 1)))),
            modelVersionProvider,
            featureSetProvider,
            new BaselineRegimeDetector());

        var generateAllocation = new GenerateAllocationProposalUseCase(
            policyProvider,
            portfolioProvider,
            new FakeTiltRuleProvider(AllocationProposalTestFixtures.CreateTiltRules()),
            new AllocationProposalService());

        var generateReport = new GenerateRegimeReportUseCase(
            new FakeReportRenderer(),
            reportStore);

        return new RunRegimeAnalysisUseCase(calculateRegime, generateAllocation, generateReport);
    }

    private static DataSnapshot CreateGoldilocksDataSnapshot(AsOfDate asOfDate)
    {
        var observationDate = new ObservationDate(new DateOnly(2026, 6, 30));
        var publicationDate = new PublicationDate(asOfDate.Value);

        return new DataSnapshot(
            asOfDate,
            new[]
            {
                Observation("ISM_PMI", EconomicDimension.Growth, 55m, observationDate, publicationDate),
                Observation("SAHM", EconomicDimension.Growth, 0.05m, observationDate, publicationDate),
                Observation("T10YIE", EconomicDimension.Inflation, 2.0m, observationDate, publicationDate),
                Observation("VIX", EconomicDimension.Risk, 14m, observationDate, publicationDate),
                Observation("YC_10Y2Y", EconomicDimension.Monetary, 0.5m, observationDate, publicationDate),
                Observation("HY_OAS", EconomicDimension.Credit, 300m, observationDate, publicationDate)
            },
            Array.Empty<MarketObservation>());
    }

    private static MacroObservation Observation(
        string code,
        EconomicDimension dimension,
        decimal value,
        ObservationDate observationDate,
        PublicationDate publicationDate)
    {
        return new MacroObservation(
            code,
            code,
            dimension,
            observationDate,
            publicationDate,
            publicationDate.Value,
            value,
            "Fixture",
            "Index");
    }

    private static FeatureSetVersion CreateFeatureSetVersion()
    {
        return new FeatureSetVersion(
            "CRS Baseline",
            "0.1",
            new[]
            {
                Feature("GROWTH_MOM", "Growth momentum", EconomicDimension.Growth, FeaturePolarity.HigherIsRiskOn),
                Feature("INFL_PRESS", "Inflation pressure", EconomicDimension.Inflation, FeaturePolarity.HigherIsRiskOff),
                Feature("RISK_APPETITE", "Risk appetite", EconomicDimension.Risk, FeaturePolarity.HigherIsRiskOn),
                Feature("MONETARY_COND", "Monetary conditions", EconomicDimension.Monetary, FeaturePolarity.HigherIsRiskOn),
                Feature("CREDIT_STRESS", "Credit stress", EconomicDimension.Credit, FeaturePolarity.HigherIsRiskOff)
            });
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

    private sealed class FakeDataSnapshotProvider(DataSnapshot snapshot) : IDataSnapshotProvider
    {
        public Task<DataSnapshot?> GetSnapshotAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            return Task.FromResult<DataSnapshot?>(snapshot);
        }
    }

    private sealed class FakeModelVersionProvider(ModelVersion? modelVersion) : IModelVersionProvider
    {
        public Task<ModelVersion?> GetActiveModelVersionAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(modelVersion);
        }
    }

    private sealed class FakeFeatureSetProvider(FeatureSetVersion? featureSetVersion) : IFeatureSetProvider
    {
        public Task<FeatureSetVersion?> GetActiveFeatureSetAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(featureSetVersion);
        }
    }

    private sealed class FakePolicyProvider(StrategicAllocationPolicy? policy) : IStrategicAllocationPolicyProvider
    {
        public Task<StrategicAllocationPolicy?> GetPolicyAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(policy);
        }
    }

    private sealed class FakePortfolioProvider(CurrentPortfolio portfolio) : ICurrentPortfolioProvider
    {
        public Task<CurrentPortfolio?> GetCurrentPortfolioAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            return Task.FromResult<CurrentPortfolio?>(portfolio);
        }
    }

    private sealed class FakeTiltRuleProvider(IReadOnlyList<RegimeTiltRule> tiltRules) : IRegimeTiltRuleProvider
    {
        public Task<IReadOnlyList<RegimeTiltRule>> GetTiltRulesAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(tiltRules);
        }
    }

    private sealed class FakeReportRenderer : IRegimeReportRenderer
    {
        public string Render(RegimeReportContent content)
        {
            return $"# Macro-Regime Report{Environment.NewLine}{Environment.NewLine}## Allocation Proposal{Environment.NewLine}Decision suggestion: {content.AllocationProposal?.Suggestion}";
        }
    }

    private sealed class FakeReportStore(string location) : IRegimeReportStore
    {
        public string? Markdown { get; private set; }

        public Task<string> SaveMarkdownAsync(DateOnly asOfDate, string markdown, CancellationToken cancellationToken = default)
        {
            Markdown = markdown;
            return Task.FromResult(location);
        }
    }

    private sealed class FakeRegimeRunStore(string location) : IRegimeRunStore
    {
        public RegimeRunDocument? SavedDocument { get; private set; }

        public Task<string> SaveAsync(RegimeRunDocument document, CancellationToken cancellationToken = default)
        {
            SavedDocument = document;
            return Task.FromResult(location);
        }

        public Task<RegimeRunDocument?> LoadAsync(DateOnly asOfDate, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(SavedDocument?.AsOfDate == asOfDate ? SavedDocument : null);
        }
    }

    private sealed class FakeManifestStore : IRegimeRunManifestStore
    {
        private readonly List<RegimeRunManifestEntry> entries = new();

        public IReadOnlyList<RegimeRunManifestEntry> Entries => entries;

        public Task UpsertAsync(RegimeRunManifestEntry entry, CancellationToken cancellationToken = default)
        {
            entries.RemoveAll(existing => existing.AsOfDate == entry.AsOfDate);
            entries.Add(entry);
            return Task.CompletedTask;
        }

        public Task<IReadOnlyList<RegimeRunManifestEntry>> ListAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<RegimeRunManifestEntry>>(entries);
        }
    }
}
