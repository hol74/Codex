using MacroRegime.Domain.Common;
using MacroRegime.Domain.Explanations;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Regimes;

public sealed record RegimeSnapshot
{
    private const decimal ProbabilitySumTolerance = 0.0001m;

    public RegimeSnapshot(
        AsOfDate asOfDate,
        ModelVersion modelVersion,
        FeatureSetVersion featureSetVersion,
        RegimeType operationalRegime,
        RegimeConfidence confidence,
        NormalizedScore compositeScore,
        string status,
        IEnumerable<RegimeProbability> probabilities,
        IEnumerable<FeatureScore> featureScores,
        IEnumerable<RegimeExplanation> explanations,
        IEnumerable<string> warnings)
    {
        if (asOfDate.Value == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "Snapshot as-of date is required.");
        }

        ArgumentNullException.ThrowIfNull(modelVersion);
        ArgumentNullException.ThrowIfNull(featureSetVersion);
        ArgumentNullException.ThrowIfNull(probabilities);
        ArgumentNullException.ThrowIfNull(featureScores);
        ArgumentNullException.ThrowIfNull(explanations);
        ArgumentNullException.ThrowIfNull(warnings);

        var orderedProbabilities = probabilities.OrderBy(probability => probability.Rank).ToArray();
        if (orderedProbabilities.Length == 0)
        {
            throw new ArgumentException("At least one regime probability is required.", nameof(probabilities));
        }

        ValidateRanks(orderedProbabilities);
        ValidateProbabilityOrder(orderedProbabilities);
        ValidateProbabilitySum(orderedProbabilities);

        AsOfDate = asOfDate;
        ModelVersion = modelVersion;
        FeatureSetVersion = featureSetVersion;
        PrimaryRegime = orderedProbabilities[0].Regime;
        OperationalRegime = operationalRegime;
        Confidence = confidence;
        CompositeScore = compositeScore;
        Status = status?.Trim() ?? string.Empty;
        Probabilities = orderedProbabilities;
        FeatureScores = featureScores.ToArray();
        Explanations = explanations.ToArray();
        Warnings = warnings.Where(warning => !string.IsNullOrWhiteSpace(warning)).Select(warning => warning.Trim()).ToArray();
    }

    public AsOfDate AsOfDate { get; }

    public ModelVersion ModelVersion { get; }

    public FeatureSetVersion FeatureSetVersion { get; }

    public RegimeType PrimaryRegime { get; }

    public RegimeType OperationalRegime { get; }

    public RegimeConfidence Confidence { get; }

    public NormalizedScore CompositeScore { get; }

    public string Status { get; }

    public IReadOnlyList<RegimeProbability> Probabilities { get; }

    public IReadOnlyList<FeatureScore> FeatureScores { get; }

    public IReadOnlyList<RegimeExplanation> Explanations { get; }

    public IReadOnlyList<string> Warnings { get; }

    private static void ValidateRanks(IReadOnlyList<RegimeProbability> orderedProbabilities)
    {
        for (var index = 0; index < orderedProbabilities.Count; index++)
        {
            var expectedRank = index + 1;
            if (orderedProbabilities[index].Rank != expectedRank)
            {
                throw new ArgumentException("Regime probability ranks must be contiguous and start at one.", nameof(orderedProbabilities));
            }
        }
    }

    private static void ValidateProbabilityOrder(IReadOnlyList<RegimeProbability> orderedProbabilities)
    {
        for (var index = 1; index < orderedProbabilities.Count; index++)
        {
            if (orderedProbabilities[index].Probability.Value > orderedProbabilities[index - 1].Probability.Value)
            {
                throw new ArgumentException("Regime probabilities must be ranked from highest to lowest probability.", nameof(orderedProbabilities));
            }
        }
    }

    private static void ValidateProbabilitySum(IReadOnlyList<RegimeProbability> orderedProbabilities)
    {
        var sum = orderedProbabilities.Sum(probability => probability.Probability.Value);
        if (Math.Abs(sum - 1m) > ProbabilitySumTolerance)
        {
            throw new ArgumentException("Regime probabilities must sum to one.", nameof(orderedProbabilities));
        }
    }
}
