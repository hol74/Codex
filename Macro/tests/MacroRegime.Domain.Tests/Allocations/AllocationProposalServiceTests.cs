using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Explanations;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Tests.Allocations;

public sealed class AllocationProposalServiceTests
{
    [Fact]
    public void Propose_AppliesRegimeTiltsAndKeepsTargetsInsideBands()
    {
        var proposal = new AllocationProposalService().Propose(
            Snapshot(RegimeType.Goldilocks),
            Policy(maximumTurnover: 0.25m),
            StrategicPortfolio(),
            new[]
            {
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GlobalEquity, 0.40m, "Constructive growth supports equity tilt."),
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GovernmentBonds, -0.20m, "Duration can be reduced in risk-on regimes."),
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.Cash, -0.10m, "Cash drag can be reduced while risk appetite is strong.")
            });

        Assert.NotEqual(DecisionSuggestion.ManualReviewRequired, proposal.Suggestion);
        Assert.Equal(1m, proposal.Lines.Sum(line => line.TargetWeight.Value));
        Assert.All(proposal.Lines, line =>
        {
            Assert.InRange(line.TargetWeight.Value, line.MinimumWeight.Value, line.MaximumWeight.Value);
        });
        Assert.Equal(0.75m, proposal.LineFor(AssetClass.GlobalEquity).TargetWeight.Value);
        Assert.Contains(proposal.ConstraintMessages, message => message.Contains("clipped", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Propose_SuspendsTiltsAndWaits_WhenOperationalRegimeIsUncertainTransition()
    {
        var proposal = new AllocationProposalService().Propose(
            Snapshot(RegimeType.UncertainTransition),
            Policy(maximumTurnover: 0.25m),
            StrategicPortfolio(),
            new[]
            {
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GlobalEquity, 0.10m, "Risk-on tilt.")
            });

        Assert.Equal(DecisionSuggestion.WaitForConfirmation, proposal.Suggestion);
        Assert.Equal(0m, proposal.Turnover.Value);
        Assert.Equal(0.60m, proposal.LineFor(AssetClass.GlobalEquity).TargetWeight.Value);
        Assert.Contains(proposal.Reasons, reason => reason.Contains("suspended", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Propose_ScalesTrades_WhenTurnoverWouldExceedPolicyMaximum()
    {
        var proposal = new AllocationProposalService().Propose(
            Snapshot(RegimeType.Goldilocks),
            Policy(maximumTurnover: 0.03m),
            StrategicPortfolio(),
            new[]
            {
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GlobalEquity, 0.08m, "Constructive growth supports equity tilt."),
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GovernmentBonds, -0.05m, "Duration can be reduced in risk-on regimes."),
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.Cash, -0.03m, "Cash drag can be reduced while risk appetite is strong.")
            });

        Assert.InRange(proposal.Turnover.Value, 0.0299m, 0.0301m);
        Assert.Contains(proposal.ConstraintMessages, message => message.Contains("Turnover exceeded", StringComparison.OrdinalIgnoreCase));
        Assert.All(proposal.Lines, line =>
        {
            Assert.InRange(line.TargetWeight.Value, line.MinimumWeight.Value, line.MaximumWeight.Value);
        });
    }

    [Fact]
    public void Propose_BlocksProposal_WhenEstimatedCostExceedsPolicyMaximum()
    {
        var proposal = new AllocationProposalService().Propose(
            Snapshot(RegimeType.Goldilocks),
            Policy(maximumTurnover: 0.25m, maximumEstimatedCost: 0.00001m),
            StrategicPortfolio(),
            new[]
            {
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GlobalEquity, 0.08m, "Constructive growth supports equity tilt."),
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GovernmentBonds, -0.05m, "Duration can be reduced in risk-on regimes."),
                new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.Cash, -0.03m, "Cash drag can be reduced while risk appetite is strong.")
            },
            estimatedCostPerTurnover: 0.01m);

        Assert.Equal(DecisionSuggestion.ManualReviewRequired, proposal.Suggestion);
        Assert.Equal(0m, proposal.Turnover.Value);
        Assert.Equal(0.60m, proposal.LineFor(AssetClass.GlobalEquity).TargetWeight.Value);
        Assert.Contains(proposal.ConstraintMessages, message => message.Contains("blocked", StringComparison.OrdinalIgnoreCase));
    }

    private static StrategicAllocationPolicy Policy(decimal maximumTurnover, decimal maximumEstimatedCost = 0.001m)
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
            new AllocationWeight(maximumTurnover),
            maximumEstimatedCost);
    }

    private static CurrentPortfolio StrategicPortfolio()
    {
        return new CurrentPortfolio(new[]
        {
            new PortfolioWeight(AssetClass.Cash, new AllocationWeight(0.05m)),
            new PortfolioWeight(AssetClass.GlobalEquity, new AllocationWeight(0.60m)),
            new PortfolioWeight(AssetClass.GovernmentBonds, new AllocationWeight(0.25m)),
            new PortfolioWeight(AssetClass.Gold, new AllocationWeight(0.10m))
        });
    }

    private static RegimeSnapshot Snapshot(RegimeType operationalRegime)
    {
        return new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            new ModelVersion("CRS Rule-Based Engine", "0.1", ModelRole.Baseline, new Dictionary<string, decimal>(), new DateOnly(2026, 7, 1), "Baseline model"),
            new FeatureSetVersion("CRS Baseline", "0.1", new[] { Feature() }),
            operationalRegime,
            new RegimeConfidence(0.70m),
            new NormalizedScore(0.65m),
            operationalRegime == RegimeType.UncertainTransition ? "Transition" : "Confirmed",
            Probabilities(operationalRegime),
            Array.Empty<FeatureScore>(),
            Array.Empty<RegimeExplanation>(),
            Array.Empty<string>());
    }

    private static FeatureDefinition Feature()
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

    private static IReadOnlyList<RegimeProbability> Probabilities(RegimeType operationalRegime)
    {
        if (operationalRegime == RegimeType.UncertainTransition)
        {
            return new[]
            {
                new RegimeProbability(RegimeType.UncertainTransition, new Probability(0.60m), 1),
                new RegimeProbability(RegimeType.Goldilocks, new Probability(0.40m), 2)
            };
        }

        return new[]
        {
            new RegimeProbability(operationalRegime, new Probability(0.70m), 1),
            new RegimeProbability(RegimeType.UncertainTransition, new Probability(0.30m), 2)
        };
    }
}
