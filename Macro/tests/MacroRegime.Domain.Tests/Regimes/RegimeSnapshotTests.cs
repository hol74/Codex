using MacroRegime.Domain.Common;
using MacroRegime.Domain.Explanations;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Tests.Regimes;

public sealed class RegimeSnapshotTests
{
    [Fact]
    public void Constructor_RequiresAsOfDate()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new RegimeSnapshot(
            default,
            CreateModelVersion(),
            CreateFeatureSetVersion(),
            RegimeType.UncertainTransition,
            new RegimeConfidence(0.6m),
            new NormalizedScore(0.55m),
            "Transition",
            CreateProbabilities(),
            Array.Empty<FeatureScore>(),
            Array.Empty<RegimeExplanation>(),
            Array.Empty<string>()));
    }

    [Fact]
    public void Constructor_RequiresModelVersion()
    {
        Assert.Throws<ArgumentNullException>(() => new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            null!,
            CreateFeatureSetVersion(),
            RegimeType.UncertainTransition,
            new RegimeConfidence(0.6m),
            new NormalizedScore(0.55m),
            "Transition",
            CreateProbabilities(),
            Array.Empty<FeatureScore>(),
            Array.Empty<RegimeExplanation>(),
            Array.Empty<string>()));
    }

    [Fact]
    public void Constructor_RequiresFeatureSetVersion()
    {
        Assert.Throws<ArgumentNullException>(() => new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            CreateModelVersion(),
            null!,
            RegimeType.UncertainTransition,
            new RegimeConfidence(0.6m),
            new NormalizedScore(0.55m),
            "Transition",
            CreateProbabilities(),
            Array.Empty<FeatureScore>(),
            Array.Empty<RegimeExplanation>(),
            Array.Empty<string>()));
    }

    [Fact]
    public void Constructor_OrdersProbabilitiesByRankAndSetsPrimaryRegime()
    {
        var snapshot = new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            CreateModelVersion(),
            CreateFeatureSetVersion(),
            RegimeType.UncertainTransition,
            new RegimeConfidence(0.6m),
            new NormalizedScore(0.55m),
            "Transition",
            CreateProbabilities().Reverse(),
            Array.Empty<FeatureScore>(),
            Array.Empty<RegimeExplanation>(),
            new[] { " confidence below threshold " });

        Assert.Equal(RegimeType.Goldilocks, snapshot.PrimaryRegime);
        Assert.Equal(new[] { 1, 2, 3 }, snapshot.Probabilities.Select(probability => probability.Rank));
        Assert.Equal(1m, snapshot.Probabilities.Sum(probability => probability.Probability.Value));
        Assert.Equal("confidence below threshold", Assert.Single(snapshot.Warnings));
    }

    [Fact]
    public void Constructor_RejectsUnnormalizedProbabilities()
    {
        var probabilities = new[]
        {
            new RegimeProbability(RegimeType.Goldilocks, new Probability(0.5m), 1),
            new RegimeProbability(RegimeType.Reflation, new Probability(0.3m), 2)
        };

        Assert.Throws<ArgumentException>(() => new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            CreateModelVersion(),
            CreateFeatureSetVersion(),
            RegimeType.UncertainTransition,
            new RegimeConfidence(0.6m),
            new NormalizedScore(0.55m),
            "Transition",
            probabilities,
            Array.Empty<FeatureScore>(),
            Array.Empty<RegimeExplanation>(),
            Array.Empty<string>()));
    }

    [Fact]
    public void Constructor_RejectsProbabilityRankThatContradictsProbabilityOrder()
    {
        var probabilities = new[]
        {
            new RegimeProbability(RegimeType.Goldilocks, new Probability(0.4m), 1),
            new RegimeProbability(RegimeType.Reflation, new Probability(0.6m), 2)
        };

        Assert.Throws<ArgumentException>(() => new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            CreateModelVersion(),
            CreateFeatureSetVersion(),
            RegimeType.UncertainTransition,
            new RegimeConfidence(0.6m),
            new NormalizedScore(0.55m),
            "Transition",
            probabilities,
            Array.Empty<FeatureScore>(),
            Array.Empty<RegimeExplanation>(),
            Array.Empty<string>()));
    }

    private static ModelVersion CreateModelVersion()
    {
        return new ModelVersion(
            "CRS Rule-Based Engine",
            "0.1",
            ModelRole.Baseline,
            new Dictionary<string, decimal>(),
            new DateOnly(2026, 7, 1),
            "Baseline model");
    }

    private static FeatureSetVersion CreateFeatureSetVersion()
    {
        return new FeatureSetVersion(
            "CRS Baseline",
            "0.1",
            new[]
            {
                new FeatureDefinition(
                    "GROWTH_MOM",
                    "Growth momentum",
                    EconomicDimension.Growth,
                    "PMI and Sahm rule blend",
                    new FeatureWeight(1m),
                    FeaturePolarity.HigherIsRiskOn,
                    6,
                    true)
            });
    }

    private static RegimeProbability[] CreateProbabilities()
    {
        return new[]
        {
            new RegimeProbability(RegimeType.Goldilocks, new Probability(0.5m), 1),
            new RegimeProbability(RegimeType.Reflation, new Probability(0.3m), 2),
            new RegimeProbability(RegimeType.UncertainTransition, new Probability(0.2m), 3)
        };
    }
}
