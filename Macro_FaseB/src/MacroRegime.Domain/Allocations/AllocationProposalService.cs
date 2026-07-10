using MacroRegime.Domain.Regimes;

namespace MacroRegime.Domain.Allocations;

public sealed class AllocationProposalService
{
    private const decimal WeightSumTolerance = 0.0001m;

    public AllocationProposal Propose(
        RegimeSnapshot snapshot,
        StrategicAllocationPolicy policy,
        CurrentPortfolio currentPortfolio,
        IEnumerable<RegimeTiltRule> tiltRules,
        decimal estimatedCostPerTurnover = 0.001m)
    {
        ArgumentNullException.ThrowIfNull(snapshot);
        ArgumentNullException.ThrowIfNull(policy);
        ArgumentNullException.ThrowIfNull(currentPortfolio);
        ArgumentNullException.ThrowIfNull(tiltRules);

        if (estimatedCostPerTurnover < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(estimatedCostPerTurnover), "Estimated cost per turnover cannot be negative.");
        }

        var reasons = new List<string>();
        var constraints = new List<string>();
        var activeTilts = SelectActiveTilts(snapshot, tiltRules, reasons);
        var targetWeights = BuildTargetWeights(policy, currentPortfolio, activeTilts, snapshot.OperationalRegime, constraints);
        var cappedTargets = CapTurnover(policy, currentPortfolio, targetWeights, constraints);
        var turnover = CalculateTurnover(policy, currentPortfolio, cappedTargets);
        var estimatedCost = turnover * estimatedCostPerTurnover;

        if (estimatedCost > policy.MaximumEstimatedCost)
        {
            constraints.Add("Estimated cost exceeds policy maximum; proposal is blocked for manual review.");
            cappedTargets = policy.Bands.ToDictionary(band => band.AssetClass, band => currentPortfolio.WeightOf(band.AssetClass));
            turnover = 0m;
            estimatedCost = 0m;
        }

        var suggestion = DetermineSuggestion(snapshot.OperationalRegime, turnover, estimatedCost, policy, constraints);
        var lines = BuildLines(policy, currentPortfolio, cappedTargets, activeTilts);

        return new AllocationProposal(
            snapshot.AsOfDate,
            snapshot.OperationalRegime,
            suggestion,
            new AllocationWeight(turnover),
            estimatedCost,
            lines,
            reasons,
            constraints);
    }

    private static IReadOnlyList<RegimeTiltRule> SelectActiveTilts(
        RegimeSnapshot snapshot,
        IEnumerable<RegimeTiltRule> tiltRules,
        List<string> reasons)
    {
        var tiltArray = tiltRules.ToArray();
        if (snapshot.OperationalRegime == RegimeType.UncertainTransition)
        {
            reasons.Add("Operational regime is UncertainTransition; active tilts are suspended pending confirmation.");
            return Array.Empty<RegimeTiltRule>();
        }

        var activeTilts = tiltArray.Where(rule => rule.Regime == snapshot.OperationalRegime).ToArray();
        reasons.AddRange(activeTilts.Select(rule => rule.Reason));
        return activeTilts;
    }

    private static Dictionary<AssetClass, decimal> BuildTargetWeights(
        StrategicAllocationPolicy policy,
        CurrentPortfolio currentPortfolio,
        IReadOnlyList<RegimeTiltRule> activeTilts,
        RegimeType operationalRegime,
        List<string> constraints)
    {
        if (operationalRegime == RegimeType.UncertainTransition)
        {
            return policy.Bands.ToDictionary(
                band => band.AssetClass,
                band => Clamp(currentPortfolio.WeightOf(band.AssetClass), band.Minimum.Value, band.Maximum.Value));
        }

        var rawTargets = policy.Bands.ToDictionary(
            band => band.AssetClass,
            band => band.Strategic.Value + activeTilts.Where(rule => rule.AssetClass == band.AssetClass).Sum(rule => rule.Tilt));

        var normalized = NormalizeWithinBands(policy, rawTargets);
        foreach (var band in policy.Bands)
        {
            if (rawTargets[band.AssetClass] < band.Minimum.Value || rawTargets[band.AssetClass] > band.Maximum.Value)
            {
                constraints.Add($"{band.AssetClass} target was clipped to policy band.");
            }
        }

        return normalized;
    }

    private static Dictionary<AssetClass, decimal> CapTurnover(
        StrategicAllocationPolicy policy,
        CurrentPortfolio currentPortfolio,
        IReadOnlyDictionary<AssetClass, decimal> targetWeights,
        List<string> constraints)
    {
        var turnover = CalculateTurnover(policy, currentPortfolio, targetWeights);
        if (turnover <= policy.MaximumTurnover.Value || turnover == 0m)
        {
            return targetWeights.ToDictionary(pair => pair.Key, pair => pair.Value);
        }

        var scale = policy.MaximumTurnover.Value / turnover;
        constraints.Add("Turnover exceeded policy maximum; target trades were scaled down.");

        return policy.Bands.ToDictionary(
            band => band.AssetClass,
            band => currentPortfolio.WeightOf(band.AssetClass)
                + ((targetWeights[band.AssetClass] - currentPortfolio.WeightOf(band.AssetClass)) * scale));
    }

    private static IReadOnlyList<AllocationProposalLine> BuildLines(
        StrategicAllocationPolicy policy,
        CurrentPortfolio currentPortfolio,
        IReadOnlyDictionary<AssetClass, decimal> targetWeights,
        IReadOnlyList<RegimeTiltRule> activeTilts)
    {
        return policy.Bands
            .Select(band =>
            {
                var currentWeight = currentPortfolio.WeightOf(band.AssetClass);
                var targetWeight = targetWeights[band.AssetClass];
                return new AllocationProposalLine(
                    band.AssetClass,
                    new AllocationWeight(currentWeight),
                    band.Strategic,
                    new AllocationWeight(targetWeight),
                    band.Minimum,
                    band.Maximum,
                    activeTilts.Where(rule => rule.AssetClass == band.AssetClass).Sum(rule => rule.Tilt),
                    targetWeight - currentWeight);
            })
            .ToArray();
    }

    private static DecisionSuggestion DetermineSuggestion(
        RegimeType operationalRegime,
        decimal turnover,
        decimal estimatedCost,
        StrategicAllocationPolicy policy,
        IReadOnlyList<string> constraints)
    {
        if (constraints.Any(message => message.Contains("blocked", StringComparison.OrdinalIgnoreCase)))
        {
            return DecisionSuggestion.ManualReviewRequired;
        }

        if (operationalRegime == RegimeType.UncertainTransition)
        {
            return DecisionSuggestion.WaitForConfirmation;
        }

        if (turnover <= 0.0001m)
        {
            return DecisionSuggestion.Hold;
        }

        if (estimatedCost > policy.MaximumEstimatedCost)
        {
            return DecisionSuggestion.ManualReviewRequired;
        }

        return turnover <= policy.MaximumTurnover.Value / 2m
            ? DecisionSuggestion.PartialRebalance
            : DecisionSuggestion.FullRebalance;
    }

    private static decimal CalculateTurnover(
        StrategicAllocationPolicy policy,
        CurrentPortfolio currentPortfolio,
        IReadOnlyDictionary<AssetClass, decimal> targetWeights)
    {
        return policy.Bands.Sum(band => Math.Abs(targetWeights[band.AssetClass] - currentPortfolio.WeightOf(band.AssetClass))) / 2m;
    }

    private static Dictionary<AssetClass, decimal> NormalizeWithinBands(
        StrategicAllocationPolicy policy,
        IReadOnlyDictionary<AssetClass, decimal> rawTargets)
    {
        var targets = policy.Bands.ToDictionary(
            band => band.AssetClass,
            band => Clamp(rawTargets[band.AssetClass], band.Minimum.Value, band.Maximum.Value));

        for (var iteration = 0; iteration < policy.Bands.Count; iteration++)
        {
            var sum = targets.Values.Sum();
            var residual = 1m - sum;
            if (Math.Abs(residual) <= WeightSumTolerance)
            {
                return targets;
            }

            if (residual > 0m)
            {
                var adjustable = policy.Bands.Where(band => targets[band.AssetClass] < band.Maximum.Value).ToArray();
                DistributeResidual(targets, adjustable, residual, useMaximumCapacity: true);
            }
            else
            {
                var adjustable = policy.Bands.Where(band => targets[band.AssetClass] > band.Minimum.Value).ToArray();
                DistributeResidual(targets, adjustable, residual, useMaximumCapacity: false);
            }
        }

        if (Math.Abs(targets.Values.Sum() - 1m) > WeightSumTolerance)
        {
            throw new InvalidOperationException("Unable to normalize allocation targets within policy bands.");
        }

        return targets;
    }

    private static void DistributeResidual(
        Dictionary<AssetClass, decimal> targets,
        IReadOnlyList<AllocationBand> adjustable,
        decimal residual,
        bool useMaximumCapacity)
    {
        if (adjustable.Count == 0)
        {
            return;
        }

        var totalCapacity = adjustable.Sum(band => useMaximumCapacity
            ? band.Maximum.Value - targets[band.AssetClass]
            : targets[band.AssetClass] - band.Minimum.Value);

        if (totalCapacity <= 0m)
        {
            return;
        }

        foreach (var band in adjustable)
        {
            var capacity = useMaximumCapacity
                ? band.Maximum.Value - targets[band.AssetClass]
                : targets[band.AssetClass] - band.Minimum.Value;

            var share = capacity / totalCapacity;
            targets[band.AssetClass] += residual * share;
            targets[band.AssetClass] = Clamp(targets[band.AssetClass], band.Minimum.Value, band.Maximum.Value);
        }
    }

    private static decimal Clamp(decimal value, decimal minimum, decimal maximum)
    {
        return Math.Min(maximum, Math.Max(minimum, value));
    }
}
