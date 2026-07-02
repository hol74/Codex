using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Explanations;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;

namespace MacroRegime.Domain.Regimes;

public sealed class BaselineRegimeDetector
{
    private readonly FeatureNormalizer featureNormalizer;
    private readonly CompositeScoreCalculator compositeScoreCalculator;
    private readonly RegimeProbabilityNormalizer probabilityNormalizer;
    private readonly RegimeExplanationBuilder explanationBuilder;

    public BaselineRegimeDetector()
        : this(
            new FeatureNormalizer(),
            new CompositeScoreCalculator(),
            new RegimeProbabilityNormalizer(),
            new RegimeExplanationBuilder())
    {
    }

    public BaselineRegimeDetector(
        FeatureNormalizer featureNormalizer,
        CompositeScoreCalculator compositeScoreCalculator,
        RegimeProbabilityNormalizer probabilityNormalizer,
        RegimeExplanationBuilder explanationBuilder)
    {
        this.featureNormalizer = featureNormalizer ?? throw new ArgumentNullException(nameof(featureNormalizer));
        this.compositeScoreCalculator = compositeScoreCalculator ?? throw new ArgumentNullException(nameof(compositeScoreCalculator));
        this.probabilityNormalizer = probabilityNormalizer ?? throw new ArgumentNullException(nameof(probabilityNormalizer));
        this.explanationBuilder = explanationBuilder ?? throw new ArgumentNullException(nameof(explanationBuilder));
    }

    public RegimeSnapshot Detect(DataSnapshot snapshot, FeatureSetVersion featureSetVersion, ModelVersion modelVersion)
    {
        ArgumentNullException.ThrowIfNull(snapshot);
        ArgumentNullException.ThrowIfNull(featureSetVersion);
        ArgumentNullException.ThrowIfNull(modelVersion);

        var parameters = BaselineRegimeParameters.From(modelVersion);
        var normalized = featureNormalizer.Normalize(snapshot, featureSetVersion);
        var featureScores = normalized.FeatureScores;
        var compositeScore = compositeScoreCalculator.Calculate(featureScores);
        var warnings = normalized.Warnings.ToList();
        var missingFeatureCount = warnings.Count(warning => warning.Contains("missing", StringComparison.OrdinalIgnoreCase));
        var divergentSignals = HasDivergentSignals(featureScores);

        if (divergentSignals)
        {
            warnings.Add("Divergent macro signals detected; operational regime set to UncertainTransition.");
        }

        if (missingFeatureCount > 0)
        {
            warnings.Add("Missing dimensions reduce regime confidence.");
        }

        var rawScores = BuildRawRegimeScores(featureScores, divergentSignals, missingFeatureCount);
        var probabilities = probabilityNormalizer.Normalize(rawScores);
        var primaryRegime = probabilities[0].Regime;
        var confidence = CalculateConfidence(probabilities, missingFeatureCount, divergentSignals);
        var operationalRegime = DetermineOperationalRegime(primaryRegime, confidence, divergentSignals, missingFeatureCount, parameters);
        var explanations = explanationBuilder.Build(primaryRegime, featureScores);

        if (confidence.Value < parameters.ConfirmationThreshold)
        {
            warnings.Add("Confidence below confirmation threshold.");
        }

        return new RegimeSnapshot(
            snapshot.AsOfDate,
            modelVersion,
            featureSetVersion,
            operationalRegime,
            confidence,
            compositeScore,
            operationalRegime == RegimeType.UncertainTransition ? "Transition" : "Confirmed",
            probabilities,
            featureScores,
            explanations,
            warnings);
    }

    private static IReadOnlyDictionary<RegimeType, decimal> BuildRawRegimeScores(
        IReadOnlyList<FeatureScore> featureScores,
        bool divergentSignals,
        int missingFeatureCount)
    {
        var growth = GetScore(featureScores, "GROWTH_MOM");
        var inflation = GetScore(featureScores, "INFL_PRESS");
        var risk = GetScore(featureScores, "RISK_APPETITE");
        var monetary = GetScore(featureScores, "MONETARY_COND");
        var credit = GetScore(featureScores, "CREDIT_STRESS");
        var inflationModerate = 1m - Math.Min(1m, Math.Abs(inflation - 0.5m) * 2m);
        var neutralSignal = CalculateNeutralSignal(new[] { growth, inflation, risk, monetary, credit });

        return new Dictionary<RegimeType, decimal>
        {
            [RegimeType.Goldilocks] = 0.15m + growth + risk + credit + inflationModerate + (monetary * 0.5m),
            [RegimeType.Reflation] = 0.15m + growth + risk + (inflation * 1.5m) + (credit * 0.5m),
            [RegimeType.LateCycleOverheating] = 0.10m + growth + (inflation * 1.2m) + (1m - monetary) + (risk * 0.5m),
            [RegimeType.Stagflation] = 0.10m + (1m - growth) + (inflation * 1.5m) + (1m - credit) + ((1m - monetary) * 0.5m),
            [RegimeType.DeflationBust] = 0.10m + (1m - growth) + (1m - inflation) + (1m - risk) + (1m - credit),
            [RegimeType.UncertainTransition] = 0.40m + (neutralSignal * 2m) + (divergentSignals ? 1.5m : 0m) + (missingFeatureCount * 0.3m)
        };
    }

    private static RegimeConfidence CalculateConfidence(
        IReadOnlyList<RegimeProbability> probabilities,
        int missingFeatureCount,
        bool divergentSignals)
    {
        var topProbability = probabilities[0].Probability.Value;
        var confidenceValue = Math.Min(1m, topProbability * 1.8m);

        if (probabilities.Count > 1 && topProbability - probabilities[1].Probability.Value < 0.03m)
        {
            confidenceValue -= 0.1m;
        }

        confidenceValue -= Math.Min(0.3m, missingFeatureCount * 0.08m);

        if (divergentSignals)
        {
            confidenceValue -= 0.2m;
        }

        return new RegimeConfidence(Math.Min(1m, Math.Max(0m, confidenceValue)));
    }

    private static RegimeType DetermineOperationalRegime(
        RegimeType primaryRegime,
        RegimeConfidence confidence,
        bool divergentSignals,
        int missingFeatureCount,
        BaselineRegimeParameters parameters)
    {
        if (divergentSignals || missingFeatureCount > 0 || confidence.Value < parameters.ConfirmationThreshold)
        {
            return RegimeType.UncertainTransition;
        }

        return primaryRegime;
    }

    private static bool HasDivergentSignals(IReadOnlyList<FeatureScore> featureScores)
    {
        var growth = GetScore(featureScores, "GROWTH_MOM");
        var inflation = GetScore(featureScores, "INFL_PRESS");
        var risk = GetScore(featureScores, "RISK_APPETITE");
        var credit = GetScore(featureScores, "CREDIT_STRESS");

        return growth > 0.65m && inflation > 0.65m && (risk < 0.40m || credit < 0.40m);
    }

    private static decimal CalculateNeutralSignal(IEnumerable<decimal> scores)
    {
        var scoreArray = scores.ToArray();
        if (scoreArray.Length == 0)
        {
            return 1m;
        }

        var averageDistance = scoreArray.Average(score => Math.Abs(score - 0.5m));
        return Math.Max(0m, 1m - (averageDistance / 0.35m));
    }

    private static decimal GetScore(IEnumerable<FeatureScore> featureScores, string code)
    {
        return featureScores
            .FirstOrDefault(score => string.Equals(score.FeatureCode, code, StringComparison.OrdinalIgnoreCase))
            ?.NormalizedScore.Value ?? NormalizedScore.Neutral.Value;
    }
}
