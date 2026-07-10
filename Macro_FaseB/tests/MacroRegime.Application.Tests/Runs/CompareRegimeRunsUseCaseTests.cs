using MacroRegime.Application.Runs;

namespace MacroRegime.Application.Tests.Runs;

public sealed class CompareRegimeRunsUseCaseTests
{
    [Fact]
    public async Task ExecuteAsync_ComparesRegimeProbabilitiesFeaturesAndAllocation()
    {
        var baseline = RegimeRunTestFixtures.CreateDocument(
            new DateOnly(2026, 7, 1),
            primaryRegime: "Goldilocks",
            primaryProbability: 0.7m,
            confidence: 0.7m,
            growthScore: 0.8m,
            allocationSuggestion: "PartialRebalance",
            equityTarget: 0.65m);
        var comparison = RegimeRunTestFixtures.CreateDocument(
            new DateOnly(2026, 8, 1),
            primaryRegime: "Reflation",
            primaryProbability: 0.6m,
            confidence: 0.55m,
            growthScore: 0.5m,
            allocationSuggestion: "Hold",
            equityTarget: 0.60m);
        var store = new InMemoryRegimeRunStore(baseline, comparison);
        var useCase = new CompareRegimeRunsUseCase(store);

        var result = await useCase.ExecuteAsync(
            new CompareRegimeRunsCommand(new DateOnly(2026, 7, 1), new DateOnly(2026, 8, 1)));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Comparison);
        Assert.True(result.Comparison.PrimaryRegimeChanged);
        Assert.True(result.Comparison.OperationalRegimeChanged);
        Assert.Equal(-0.15m, result.Comparison.ConfidenceDelta);

        var goldilocksDelta = Assert.Single(result.Comparison.ProbabilityDeltas, delta => delta.Regime == "Goldilocks");
        Assert.Equal(0.7m, goldilocksDelta.BaselineProbability);
        Assert.Equal(0.4m, goldilocksDelta.ComparisonProbability);
        Assert.Equal(-0.3m, goldilocksDelta.Delta);

        var growthDelta = Assert.Single(result.Comparison.FeatureDeltas, delta => delta.FeatureCode == "GROWTH_MOM");
        Assert.Equal(-0.3m, growthDelta.Delta);

        Assert.NotNull(result.Comparison.Allocation);
        Assert.True(result.Comparison.Allocation.SuggestionChanged);
        Assert.Equal("PartialRebalance", result.Comparison.Allocation.BaselineSuggestion);
        Assert.Equal("Hold", result.Comparison.Allocation.ComparisonSuggestion);

        var equityDelta = Assert.Single(result.Comparison.Allocation.LineDeltas, delta => delta.AssetClass == "GlobalEquity");
        Assert.Equal(-0.05m, equityDelta.Delta);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsNullAllocationComparison_WhenNeitherRunHasAllocation()
    {
        var baseline = RegimeRunTestFixtures.CreateDocument(new DateOnly(2026, 7, 1)) with { Allocation = null };
        var comparison = RegimeRunTestFixtures.CreateDocument(new DateOnly(2026, 8, 1)) with { Allocation = null };
        var useCase = new CompareRegimeRunsUseCase(new InMemoryRegimeRunStore(baseline, comparison));

        var result = await useCase.ExecuteAsync(
            new CompareRegimeRunsCommand(new DateOnly(2026, 7, 1), new DateOnly(2026, 8, 1)));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Comparison);
        Assert.Null(result.Comparison.Allocation);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsFailure_WhenBaselineRunIsMissing()
    {
        var comparison = RegimeRunTestFixtures.CreateDocument(new DateOnly(2026, 8, 1));
        var useCase = new CompareRegimeRunsUseCase(new InMemoryRegimeRunStore(comparison));

        var result = await useCase.ExecuteAsync(
            new CompareRegimeRunsCommand(new DateOnly(2026, 7, 1), new DateOnly(2026, 8, 1)));

        Assert.False(result.IsSuccess);
        Assert.Contains("baseline", result.Error);
        Assert.Contains("2026-07-01", result.Error);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsFailure_WhenComparisonRunIsMissing()
    {
        var baseline = RegimeRunTestFixtures.CreateDocument(new DateOnly(2026, 7, 1));
        var useCase = new CompareRegimeRunsUseCase(new InMemoryRegimeRunStore(baseline));

        var result = await useCase.ExecuteAsync(
            new CompareRegimeRunsCommand(new DateOnly(2026, 7, 1), new DateOnly(2026, 8, 1)));

        Assert.False(result.IsSuccess);
        Assert.Contains("comparison", result.Error);
        Assert.Contains("2026-08-01", result.Error);
    }
}
