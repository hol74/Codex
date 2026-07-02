using MacroRegime.Domain.Common;

namespace MacroRegime.Domain.Regimes;

public sealed class RegimeProbabilityNormalizer
{
    public IReadOnlyList<RegimeProbability> Normalize(IReadOnlyDictionary<RegimeType, decimal> rawScores)
    {
        ArgumentNullException.ThrowIfNull(rawScores);

        if (rawScores.Count == 0)
        {
            throw new ArgumentException("At least one raw regime score is required.", nameof(rawScores));
        }

        foreach (var rawScore in rawScores)
        {
            if (rawScore.Value < 0m)
            {
                throw new ArgumentOutOfRangeException(nameof(rawScores), "Raw regime scores cannot be negative.");
            }
        }

        var total = rawScores.Values.Sum();
        var probabilities = total == 0m
            ? BuildUniformProbabilities(rawScores.Keys)
            : rawScores.Select(score => new RegimeProbabilityValue(score.Key, score.Value / total)).ToArray();

        return Rank(AdjustToOne(probabilities));
    }

    private static RegimeProbabilityValue[] BuildUniformProbabilities(IEnumerable<RegimeType> regimes)
    {
        var regimeArray = regimes.ToArray();
        var probability = 1m / regimeArray.Length;

        return regimeArray
            .Select(regime => new RegimeProbabilityValue(regime, probability))
            .ToArray();
    }

    private static RegimeProbabilityValue[] AdjustToOne(IReadOnlyList<RegimeProbabilityValue> probabilities)
    {
        var adjusted = probabilities.ToArray();
        var remainder = 1m - adjusted.Sum(probability => probability.Value);

        adjusted[0] = adjusted[0] with { Value = adjusted[0].Value + remainder };
        return adjusted;
    }

    private static IReadOnlyList<RegimeProbability> Rank(IEnumerable<RegimeProbabilityValue> probabilities)
    {
        return probabilities
            .OrderByDescending(probability => probability.Value)
            .ThenBy(probability => probability.Regime.ToString(), StringComparer.Ordinal)
            .Select((probability, index) => new RegimeProbability(probability.Regime, new Probability(probability.Value), index + 1))
            .ToArray();
    }

    private sealed record RegimeProbabilityValue(RegimeType Regime, decimal Value);
}
