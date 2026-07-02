using MacroRegime.Domain.Regimes;

namespace MacroRegime.Infrastructure.Persistence;

public static class RegimeRunRecordMapper
{
    public static RegimeRunRecord FromSnapshot(RegimeSnapshot snapshot)
    {
        ArgumentNullException.ThrowIfNull(snapshot);

        return new RegimeRunRecord(
            snapshot.AsOfDate.Value,
            snapshot.ModelVersion.Name,
            snapshot.ModelVersion.Version,
            snapshot.FeatureSetVersion.Name,
            snapshot.FeatureSetVersion.Version,
            snapshot.PrimaryRegime.ToString(),
            snapshot.OperationalRegime.ToString(),
            snapshot.Confidence.Value,
            snapshot.CompositeScore.Value,
            snapshot.Status,
            snapshot.Probabilities
                .Select(probability => new RegimeProbabilityRecord(
                    probability.Regime.ToString(),
                    probability.Probability.Value,
                    probability.Rank))
                .ToArray(),
            snapshot.FeatureScores
                .Select(score => new FeatureScoreRecord(
                    score.FeatureCode,
                    score.Name,
                    score.Dimension.ToString(),
                    score.Weight.Value,
                    score.RawValue,
                    score.NormalizedScore.Value,
                    score.ZScore,
                    score.Momentum,
                    score.Interpretation))
                .ToArray(),
            snapshot.Explanations
                .Select(explanation => new RegimeExplanationRecord(
                    explanation.Title,
                    explanation.Detail,
                    explanation.Impact,
                    explanation.FeatureCode,
                    explanation.Kind.ToString()))
                .ToArray(),
            snapshot.Warnings.ToArray());
    }
}
