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
        var divergentSignals = HasDivergentSignals(featureScores, parameters);

        if (divergentSignals)
        {
            warnings.Add("Divergent macro signals detected; operational regime set to UncertainTransition.");
        }

        if (missingFeatureCount > 0)
        {
            warnings.Add("Missing dimensions reduce regime confidence.");
        }

        var rawScores = BuildRawRegimeScores(featureScores, divergentSignals, missingFeatureCount, parameters);
        var probabilities = probabilityNormalizer.Normalize(rawScores);
        var primaryRegime = probabilities[0].Regime;
        var confidence = CalculateConfidence(probabilities, rawScores, missingFeatureCount, divergentSignals, parameters);
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
        int missingFeatureCount,
        BaselineRegimeParameters parameters)
    {
        if (parameters.ScoringProfile is 12m or 14m)
        {
            return BuildArchetypeDistanceScores(featureScores, divergentSignals, missingFeatureCount, parameters);
        }

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

    private static IReadOnlyDictionary<RegimeType, decimal> BuildArchetypeDistanceScores(
        IReadOnlyList<FeatureScore> featureScores,
        bool divergentSignals,
        int missingFeatureCount,
        BaselineRegimeParameters parameters)
    {
        var actual = new[]
        {
            GetScore(featureScores, "GROWTH_MOM"),
            GetScore(featureScores, "INFL_PRESS"),
            GetScore(featureScores, "RISK_APPETITE"),
            GetScore(featureScores, "MONETARY_COND"),
            GetScore(featureScores, "CREDIT_STRESS")
        };
        var neutralSignal = CalculateNeutralSignal(actual);

        var usesTranslatedRiskAnchors = parameters.ScoringProfile == 14m;
        var scores = new Dictionary<RegimeType, decimal>
        {
            [RegimeType.Goldilocks] = ArchetypeFit(actual, new[] { 0.80m, 0.40m, usesTranslatedRiskAnchors ? 0.58488439m : 0.80m, 0.75m, 0.80m }),
            [RegimeType.Reflation] = ArchetypeFit(actual, new[] { 0.70m, 0.70m, usesTranslatedRiskAnchors ? 0.48571817m : 0.70m, 0.65m, 0.70m }),
            [RegimeType.LateCycleOverheating] = ArchetypeFit(actual, new[] { 0.85m, 0.85m, usesTranslatedRiskAnchors ? 0.34138172m : 0.55m, 0.25m, 0.55m }),
            [RegimeType.Stagflation] = ArchetypeFit(actual, new[] { 0.20m, 0.85m, usesTranslatedRiskAnchors ? 0.13503642m : 0.25m, 0.30m, 0.25m }),
            [RegimeType.DeflationBust] = ArchetypeFit(actual, new[] { 0.15m, 0.15m, usesTranslatedRiskAnchors ? 0.09473512m : 0.15m, 0.35m, 0.15m }),
            [RegimeType.UncertainTransition] = Math.Min(
                1m,
                0.15m + (neutralSignal * 0.25m) + (divergentSignals ? 0.40m : 0m) + (missingFeatureCount * 0.15m))
        };

        return scores.ToDictionary(pair => pair.Key, pair => pair.Value * pair.Value);
    }

    private static decimal ArchetypeFit(IReadOnlyList<decimal> actual, IReadOnlyList<decimal> target)
    {
        var averageDistance = actual.Zip(target, (value, expected) => Math.Abs(value - expected)).Average();
        return Math.Max(0.05m, 1m - averageDistance);
    }

    private static RegimeConfidence CalculateConfidence(
        IReadOnlyList<RegimeProbability> probabilities,
        IReadOnlyDictionary<RegimeType, decimal> rawScores,
        int missingFeatureCount,
        bool divergentSignals,
        BaselineRegimeParameters parameters)
    {
        if (parameters.ScoringProfile is 12m or 14m)
        {
            return CalculateArchetypeConfidence(rawScores, missingFeatureCount, divergentSignals, parameters);
        }

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

    private static RegimeConfidence CalculateArchetypeConfidence(
        IReadOnlyDictionary<RegimeType, decimal> rawScores,
        int missingFeatureCount,
        bool divergentSignals,
        BaselineRegimeParameters parameters)
    {
        var rankedPrimaryScores = rawScores
            .Where(pair => pair.Key != RegimeType.UncertainTransition)
            .Select(pair => pair.Value)
            .OrderDescending()
            .ToArray();
        if (parameters.ScoringProfile == 14m)
        {
            var topFit = (decimal)Math.Sqrt((double)rankedPrimaryScores[0]);
            var secondFit = (decimal)Math.Sqrt((double)rankedPrimaryScores[1]);
            var separationDenominator = 1m - secondFit;
            var relativeSeparation = separationDenominator > 0m
                ? (topFit - secondFit) / separationDenominator
                : 0m;
            var geometricConfidence = (topFit * parameters.ConfidenceFitWeight)
                + (relativeSeparation * parameters.ConfidenceMarginWeight)
                - Math.Min(0.3m, missingFeatureCount * 0.08m)
                - (divergentSignals ? 0.2m : 0m);
            return new RegimeConfidence(Math.Min(1m, Math.Max(0m, geometricConfidence)));
        }

        var fit = rankedPrimaryScores[0];
        var margin = fit - rankedPrimaryScores[1];
        var confidenceValue = (fit * parameters.ConfidenceFitWeight)
            + (margin * parameters.ConfidenceMarginWeight)
            - Math.Min(0.3m, missingFeatureCount * 0.08m)
            - (divergentSignals ? 0.2m : 0m);

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

    private static bool HasDivergentSignals(
        IReadOnlyList<FeatureScore> featureScores,
        BaselineRegimeParameters parameters)
    {
        var growth = GetScore(featureScores, "GROWTH_MOM");
        var inflation = GetScore(featureScores, "INFL_PRESS");
        var risk = GetScore(featureScores, "RISK_APPETITE");
        var credit = GetScore(featureScores, "CREDIT_STRESS");

        var riskThreshold = parameters.ScoringProfile == 14m ? 0.22146613m : 0.40m;
        return growth > 0.65m && inflation > 0.65m && (risk < riskThreshold || credit < 0.40m);
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
