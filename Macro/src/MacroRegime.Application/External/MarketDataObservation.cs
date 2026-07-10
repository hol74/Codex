namespace MacroRegime.Application.External;

public sealed record MarketDataObservation(
    string ProviderSymbol,
    string Symbol,
    DateOnly ObservationDate,
    DateOnly AvailabilityDate,
    decimal Value,
    string Unit);
