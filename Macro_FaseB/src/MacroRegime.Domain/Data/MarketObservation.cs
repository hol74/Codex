using MacroRegime.Domain.Common;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Data;

public sealed record MarketObservation
{
    public MarketObservation(
        string symbol,
        string name,
        EconomicDimension dimension,
        ObservationDate observationDate,
        AvailabilityDate availabilityDate,
        decimal value,
        string source,
        string unit,
        string proxyRole)
    {
        if (string.IsNullOrWhiteSpace(symbol))
        {
            throw new ArgumentException("Market symbol is required.", nameof(symbol));
        }

        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Market observation name is required.", nameof(name));
        }

        Symbol = symbol.Trim();
        Name = name.Trim();
        Dimension = dimension;
        ObservationDate = observationDate;
        AvailabilityDate = availabilityDate;
        Value = value;
        Source = source?.Trim() ?? string.Empty;
        Unit = unit?.Trim() ?? string.Empty;
        ProxyRole = proxyRole?.Trim() ?? string.Empty;
    }

    public string Symbol { get; }

    public string Name { get; }

    public EconomicDimension Dimension { get; }

    public ObservationDate ObservationDate { get; }

    public AvailabilityDate AvailabilityDate { get; }

    public decimal Value { get; }

    public string Source { get; }

    public string Unit { get; }

    public string ProxyRole { get; }
}
