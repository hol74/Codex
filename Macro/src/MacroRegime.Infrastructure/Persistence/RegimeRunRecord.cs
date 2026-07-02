namespace MacroRegime.Infrastructure.Persistence;

public sealed record RegimeRunRecord(
    int SchemaVersion,
    DateOnly AsOfDate,
    string ModelName,
    string ModelVersion,
    string FeatureSetName,
    string FeatureSetVersion,
    string PrimaryRegime,
    string OperationalRegime,
    decimal Confidence,
    decimal CompositeScore,
    string Status,
    IReadOnlyList<RegimeProbabilityRecord> Probabilities,
    IReadOnlyList<FeatureScoreRecord> FeatureScores,
    IReadOnlyList<RegimeExplanationRecord> Explanations,
    IReadOnlyList<string> Warnings);

public sealed record RegimeProbabilityRecord(
    string Regime,
    decimal Probability,
    int Rank);

public sealed record FeatureScoreRecord(
    string FeatureCode,
    string Name,
    string Dimension,
    decimal Weight,
    decimal RawValue,
    decimal NormalizedScore,
    decimal? ZScore,
    decimal? Momentum,
    string Interpretation);

public sealed record RegimeExplanationRecord(
    string Title,
    string Detail,
    decimal Impact,
    string? FeatureCode,
    string Kind);
