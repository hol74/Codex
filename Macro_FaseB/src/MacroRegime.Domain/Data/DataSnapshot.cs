using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Data;

public sealed record DataSnapshot
{
    public DataSnapshot(
        AsOfDate asOfDate,
        IEnumerable<MacroObservation> macroObservations,
        IEnumerable<MarketObservation> marketObservations)
    {
        if (asOfDate.Value == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "Snapshot as-of date is required.");
        }

        ArgumentNullException.ThrowIfNull(macroObservations);
        ArgumentNullException.ThrowIfNull(marketObservations);

        AsOfDate = asOfDate;
        MacroObservations = macroObservations.ToArray();
        MarketObservations = marketObservations.ToArray();
    }

    public AsOfDate AsOfDate { get; }

    public IReadOnlyList<MacroObservation> MacroObservations { get; }

    public IReadOnlyList<MarketObservation> MarketObservations { get; }

    public bool TryGetValue(string code, out decimal value)
    {
        var macroObservation = MacroObservations
            .Where(observation => observation.PublicationDate.IsAvailableAt(AsOfDate))
            .Where(observation => string.Equals(observation.SeriesCode, code, StringComparison.OrdinalIgnoreCase))
            .OrderByDescending(observation => observation.PublicationDate.Value)
            .ThenByDescending(observation => observation.ObservationDate.Value)
            .FirstOrDefault();

        if (macroObservation is not null)
        {
            value = macroObservation.Value;
            return true;
        }

        var marketObservation = MarketObservations
            .Where(observation => observation.AvailabilityDate.IsAvailableAt(AsOfDate))
            .Where(observation => string.Equals(observation.Symbol, code, StringComparison.OrdinalIgnoreCase))
            .OrderByDescending(observation => observation.AvailabilityDate.Value)
            .ThenByDescending(observation => observation.ObservationDate.Value)
            .FirstOrDefault();

        if (marketObservation is not null)
        {
            value = marketObservation.Value;
            return true;
        }

        value = 0m;
        return false;
    }
}
