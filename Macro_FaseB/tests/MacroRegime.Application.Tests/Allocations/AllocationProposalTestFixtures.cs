using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Explanations;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Tests.Allocations;

internal static class AllocationProposalTestFixtures
{
    public static RegimeSnapshot CreateSnapshot()
    {
        return new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            new ModelVersion("CRS Rule-Based Engine", "0.1", ModelRole.Baseline, new Dictionary<string, decimal>(), new DateOnly(2026, 7, 1), "Baseline model"),
            new FeatureSetVersion("CRS Baseline", "0.1", new[] { CreateFeature() }),
            RegimeType.Goldilocks,
            new RegimeConfidence(0.70m),
            new NormalizedScore(0.65m),
            "Confirmed",
            new[]
            {
                new RegimeProbability(RegimeType.Goldilocks, new Probability(0.70m), 1),
                new RegimeProbability(RegimeType.UncertainTransition, new Probability(0.30m), 2)
            },
            Array.Empty<FeatureScore>(),
            Array.Empty<RegimeExplanation>(),
            Array.Empty<string>());
    }

    public static StrategicAllocationPolicy CreatePolicy()
    {
        return new StrategicAllocationPolicy(
            "Balanced IPS",
            new[]
            {
                new AllocationBand(AssetClass.Cash, new AllocationWeight(0.02m), new AllocationWeight(0.05m), new AllocationWeight(0.20m)),
                new AllocationBand(AssetClass.GlobalEquity, new AllocationWeight(0.45m), new AllocationWeight(0.60m), new AllocationWeight(0.75m)),
                new AllocationBand(AssetClass.GovernmentBonds, new AllocationWeight(0.10m), new AllocationWeight(0.25m), new AllocationWeight(0.40m)),
                new AllocationBand(AssetClass.Gold, new AllocationWeight(0.00m), new AllocationWeight(0.10m), new AllocationWeight(0.20m))
            },
            new AllocationWeight(0.25m),
            0.001m);
    }

    public static CurrentPortfolio CreatePortfolio()
    {
        return new CurrentPortfolio(new[]
        {
            new PortfolioWeight(AssetClass.Cash, new AllocationWeight(0.05m)),
            new PortfolioWeight(AssetClass.GlobalEquity, new AllocationWeight(0.60m)),
            new PortfolioWeight(AssetClass.GovernmentBonds, new AllocationWeight(0.25m)),
            new PortfolioWeight(AssetClass.Gold, new AllocationWeight(0.10m))
        });
    }

    public static IReadOnlyList<RegimeTiltRule> CreateTiltRules()
    {
        return new[]
        {
            new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GlobalEquity, 0.08m, "Constructive growth supports equity tilt."),
            new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GovernmentBonds, -0.05m, "Duration can be reduced in risk-on regimes."),
            new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.Cash, -0.03m, "Cash drag can be reduced while risk appetite is strong.")
        };
    }

    private static FeatureDefinition CreateFeature()
    {
        return new FeatureDefinition(
            "GROWTH_MOM",
            "Growth momentum",
            EconomicDimension.Growth,
            "Fixture",
            new FeatureWeight(1m),
            FeaturePolarity.HigherIsRiskOn,
            6,
            true);
    }
}
