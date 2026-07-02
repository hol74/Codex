namespace MacroRegime.Infrastructure.Import;

public sealed record JsonDataSnapshotRecord(
    int SchemaVersion,
    DateOnly AsOfDate,
    IReadOnlyList<JsonMacroObservationRecord>? MacroObservations,
    IReadOnlyList<JsonMarketObservationRecord>? MarketObservations);

public sealed record JsonMacroObservationRecord(
    string? SeriesCode,
    string? Name,
    string? Dimension,
    DateOnly ObservationDate,
    DateOnly PublicationDate,
    DateOnly? VintageDate,
    decimal Value,
    string? Source,
    string? Unit);

public sealed record JsonMarketObservationRecord(
    string? Symbol,
    string? Name,
    string? Dimension,
    DateOnly ObservationDate,
    DateOnly AvailabilityDate,
    decimal Value,
    string? Source,
    string? Unit,
    string? ProxyRole);
