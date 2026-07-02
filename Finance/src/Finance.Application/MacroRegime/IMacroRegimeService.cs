namespace Finance.Application.MacroRegime;

public interface IMacroRegimeService
{
    Task<MacroRegimeDashboard?> GetDashboardAsync(CancellationToken cancellationToken = default);
}

public sealed record MacroRegimeDashboard(
    DateOnly AsOfDate,
    string ModelName,
    string ModelVersion,
    string PrimaryRegime,
    string Status,
    decimal Confidence,
    decimal CompositeScore,
    string Summary,
    RegimeReportReadModel? Report,
    IReadOnlyCollection<RegimeProbabilityReadModel> Probabilities,
    IReadOnlyCollection<MacroFeatureReadModel> Features,
    IReadOnlyCollection<RegimeExplanationReadModel> Explanations,
    IReadOnlyCollection<MacroSeriesReadModel> Series,
    IReadOnlyCollection<MarketSeriesReadModel> MarketSeries,
    IReadOnlyCollection<ReleaseCalendarReadModel> ReleaseCalendar);

public sealed record RegimeReportReadModel(
    string Title,
    DateOnly ReportDate,
    string Narrative,
    string RecommendedAction,
    bool ReviewRequired);

public sealed record RegimeProbabilityReadModel(
    string Regime,
    decimal Probability,
    int Rank);

public sealed record MacroFeatureReadModel(
    string Code,
    string Name,
    string Dimension,
    decimal Weight,
    decimal RawValue,
    decimal NormalizedValue,
    decimal ZScore,
    decimal Momentum4Weeks,
    string Interpretation);

public sealed record RegimeExplanationReadModel(
    string Title,
    string Detail,
    decimal Impact,
    string? FeatureCode);

public sealed record MacroSeriesReadModel(
    string Code,
    string Name,
    string Category,
    string SourceName,
    DateOnly ObservationDate,
    DateOnly PublishedDate,
    decimal Value,
    string? Unit,
    string? Vintage);

public sealed record MarketSeriesReadModel(
    string Symbol,
    string Name,
    string Category,
    string SourceName,
    DateOnly Date,
    DateOnly AvailableDate,
    decimal Value,
    string? Unit,
    string? ProxyRole);

public sealed record ReleaseCalendarReadModel(
    string ReleaseCode,
    string Name,
    string SourceName,
    DateOnly ReleaseDate,
    DateOnly? ObservationPeriodStart,
    DateOnly? ObservationPeriodEnd,
    string Frequency,
    string Status);
