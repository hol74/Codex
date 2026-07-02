namespace MacroRegime.Domain.Features;

public sealed record FeatureNormalizationResult(
    IReadOnlyList<FeatureScore> FeatureScores,
    IReadOnlyList<string> Warnings);
