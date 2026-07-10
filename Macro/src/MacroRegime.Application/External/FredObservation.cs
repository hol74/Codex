namespace MacroRegime.Application.External;

public sealed record FredObservation(
    string SeriesId,
    string SeriesCode,
    DateOnly ObservationDate,
    DateOnly PublicationDate,
    DateOnly VintageDate,
    decimal Value,
    string Unit);
