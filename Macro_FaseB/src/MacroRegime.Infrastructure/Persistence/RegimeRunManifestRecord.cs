namespace MacroRegime.Infrastructure.Persistence;

public sealed record RegimeRunManifestRecord(
    int SchemaVersion,
    IReadOnlyList<RegimeRunManifestEntryRecord> Entries);

public sealed record RegimeRunManifestEntryRecord(
    DateOnly AsOfDate,
    string RunLocation,
    string ReportLocation,
    string DataSourceKind,
    string DataSourceDescription,
    string? DataSourceReference,
    string ModelName,
    string ModelVersion,
    string FeatureSetName,
    string FeatureSetVersion,
    string PrimaryRegime,
    string OperationalRegime,
    decimal Confidence,
    decimal CompositeScore,
    string Status,
    string AllocationSuggestion,
    decimal Turnover,
    decimal EstimatedCost,
    int WarningCount);
