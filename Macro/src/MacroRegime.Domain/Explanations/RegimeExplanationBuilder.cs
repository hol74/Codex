using MacroRegime.Domain.Features;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Domain.Explanations;

public sealed class RegimeExplanationBuilder
{
    private const decimal NeutralScore = 0.5m;

    public IReadOnlyList<RegimeExplanation> Build(
        RegimeType primaryRegime,
        IEnumerable<FeatureScore> featureScores,
        int maxDrivers = 3,
        int maxContrarySignals = 3)
    {
        return BuildDrivers(featureScores, maxDrivers)
            .Concat(BuildContrarySignals(primaryRegime, featureScores, maxContrarySignals))
            .ToArray();
    }

    public IReadOnlyList<RegimeExplanation> BuildDrivers(IEnumerable<FeatureScore> featureScores, int maxCount = 3)
    {
        return RankContributions(featureScores, maxCount)
            .Select(contribution => new RegimeExplanation(
                $"{contribution.FeatureScore.Name} is a driver",
                BuildDetail(contribution.FeatureScore),
                contribution.Impact,
                contribution.FeatureScore.FeatureCode,
                RegimeExplanationKind.Driver))
            .ToArray();
    }

    public IReadOnlyList<RegimeExplanation> BuildContrarySignals(
        RegimeType primaryRegime,
        IEnumerable<FeatureScore> featureScores,
        int maxCount = 3)
    {
        var expectedDirection = GetExpectedDirection(primaryRegime);
        if (expectedDirection is null)
        {
            return Array.Empty<RegimeExplanation>();
        }

        return RankContributions(featureScores, maxCount, contribution => contribution.Direction != expectedDirection)
            .Select(contribution => new RegimeExplanation(
                $"{contribution.FeatureScore.Name} is a contrary signal",
                BuildDetail(contribution.FeatureScore),
                contribution.Impact,
                contribution.FeatureScore.FeatureCode,
                RegimeExplanationKind.ContrarySignal))
            .ToArray();
    }

    private static IReadOnlyList<FeatureContribution> RankContributions(
        IEnumerable<FeatureScore> featureScores,
        int maxCount,
        Func<FeatureContribution, bool>? predicate = null)
    {
        ArgumentNullException.ThrowIfNull(featureScores);

        if (maxCount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(maxCount), "Maximum count cannot be negative.");
        }

        return featureScores
            .Select(ToContribution)
            .Where(contribution => contribution.Impact > 0m)
            .Where(contribution => predicate?.Invoke(contribution) ?? true)
            .OrderByDescending(contribution => contribution.Impact)
            .ThenBy(contribution => contribution.FeatureScore.FeatureCode, StringComparer.Ordinal)
            .Take(maxCount)
            .ToArray();
    }

    private static FeatureContribution ToContribution(FeatureScore featureScore)
    {
        var distanceFromNeutral = featureScore.NormalizedScore.Value - NeutralScore;
        var impact = Math.Abs(distanceFromNeutral) * featureScore.Weight.Value;
        var direction = distanceFromNeutral >= 0m ? FeatureSignalDirection.RiskOn : FeatureSignalDirection.RiskOff;

        return new FeatureContribution(featureScore, impact, direction);
    }

    private static FeatureSignalDirection? GetExpectedDirection(RegimeType regime)
    {
        return regime switch
        {
            RegimeType.ExpansionRiskOn => FeatureSignalDirection.RiskOn,
            RegimeType.InflationaryExpansion => FeatureSignalDirection.RiskOn,
            RegimeType.Recovery => FeatureSignalDirection.RiskOn,
            RegimeType.Goldilocks => FeatureSignalDirection.RiskOn,
            RegimeType.Reflation => FeatureSignalDirection.RiskOn,
            RegimeType.LateCycleOverheating => FeatureSignalDirection.RiskOn,
            RegimeType.Slowdown => FeatureSignalDirection.RiskOff,
            RegimeType.RecessionStress => FeatureSignalDirection.RiskOff,
            RegimeType.Stagflation => FeatureSignalDirection.RiskOff,
            RegimeType.DeflationBust => FeatureSignalDirection.RiskOff,
            _ => null
        };
    }

    private static string BuildDetail(FeatureScore featureScore)
    {
        return $"Normalized score {featureScore.NormalizedScore.Value:0.####} with weight {featureScore.Weight.Value:0.####}.";
    }

    private sealed record FeatureContribution(FeatureScore FeatureScore, decimal Impact, FeatureSignalDirection Direction);

    private enum FeatureSignalDirection
    {
        RiskOn,
        RiskOff
    }
}
