namespace Finance.Application.MacroRegime;

public interface IMacroDataFoundationService
{
    Task<MacroDataFoundationDashboard> GetDashboardAsync(DateOnly? asOfDate = null, CancellationToken cancellationToken = default);

    Task<MacroDataImportResult> ImportFredObservationsAsync(FredObservationImportRequest request, CancellationToken cancellationToken = default);

    Task<MacroDataImportResult> ImportFredMdCsvAsync(FredMdCsvImportRequest request, CancellationToken cancellationToken = default);

    Task<MacroDataImportResult> ImportMarketObservationsAsync(MarketObservationImportRequest request, CancellationToken cancellationToken = default);

    Task<AsOfDataSnapshot> GetAsOfSnapshotAsync(DateOnly asOfDate, CancellationToken cancellationToken = default);
}

public sealed record FredObservationImportRequest(
    string SeriesCode,
    DateOnly ObservationStart,
    DateOnly ObservationEnd,
    DateOnly RealtimeStart,
    DateOnly RealtimeEnd,
    string? ApiKey);

public sealed record FredMdCsvImportRequest(
    string CsvContent,
    DateOnly VintageDate,
    DateOnly PublishedDate,
    IReadOnlyDictionary<string, string> ColumnToSeriesCode);

public sealed record MarketObservationImportRequest(
    string Symbol,
    IReadOnlyCollection<MarketObservationInput> Observations,
    string SourceSystem);

public sealed record MarketObservationInput(
    DateOnly Date,
    decimal Value,
    DateOnly AvailableDate,
    string? SourceHash = null,
    string? Notes = null);

public sealed record MacroDataFoundationDashboard(
    DateOnly SnapshotDate,
    IReadOnlyCollection<MacroDataSourceCatalogItem> DataSources,
    IReadOnlyCollection<MacroSeriesCatalogItem> MacroSeries,
    IReadOnlyCollection<MarketSeriesCatalogItem> MarketSeries,
    IReadOnlyCollection<ReleaseCalendarCatalogItem> ReleaseCalendar,
    IReadOnlyCollection<ImportBatchCatalogItem> ImportBatches,
    AsOfDataSnapshot Snapshot);

public sealed record MacroDataSourceCatalogItem(
    string Name,
    string Kind,
    bool SupportsVintageData,
    int MacroSeriesCount,
    int MarketSeriesCount,
    string? Url);

public sealed record MacroSeriesCatalogItem(
    string Code,
    string Name,
    string Category,
    string Frequency,
    string SourceName,
    bool RequiresVintageTracking,
    int ObservationCount,
    DateOnly? LatestObservationDate,
    DateOnly? LatestVintageDate);

public sealed record MarketSeriesCatalogItem(
    string Symbol,
    string Name,
    string Category,
    string Frequency,
    string SourceName,
    string? ProxyRole,
    int ObservationCount,
    DateOnly? LatestDate,
    DateOnly? LatestAvailableDate);

public sealed record ReleaseCalendarCatalogItem(
    string ReleaseCode,
    string Name,
    string SourceName,
    DateOnly ReleaseDate,
    string Frequency,
    string Status);

public sealed record ImportBatchCatalogItem(
    DateTimeOffset ImportedAt,
    string SourceName,
    int RecordsRead,
    int RecordsAccepted,
    int RecordsRejected,
    string? FileName);

public sealed record MacroDataImportResult(
    string Source,
    int RecordsRead,
    int RecordsAccepted,
    int RecordsRejected,
    IReadOnlyCollection<string> Messages);

public sealed record AsOfDataSnapshot(
    DateOnly AsOfDate,
    IReadOnlyCollection<AsOfMacroObservation> MacroObservations,
    IReadOnlyCollection<AsOfMarketObservation> MarketObservations);

public sealed record AsOfMacroObservation(
    string SeriesCode,
    string Name,
    string Category,
    DateOnly ObservationDate,
    DateOnly PublishedDate,
    DateOnly VintageDate,
    decimal Value,
    string SourceSystem);

public sealed record AsOfMarketObservation(
    string Symbol,
    string Name,
    string Category,
    DateOnly Date,
    DateOnly AvailableDate,
    decimal Value,
    string SourceSystem);
