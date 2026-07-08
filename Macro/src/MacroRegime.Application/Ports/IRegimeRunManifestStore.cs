namespace MacroRegime.Application.Ports;

public interface IRegimeRunManifestStore
{
    Task UpsertAsync(RegimeRunManifestEntry entry, CancellationToken cancellationToken = default);

    Task<IReadOnlyList<RegimeRunManifestEntry>> ListAsync(CancellationToken cancellationToken = default);
}

public sealed record RegimeRunManifestEntry(
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
