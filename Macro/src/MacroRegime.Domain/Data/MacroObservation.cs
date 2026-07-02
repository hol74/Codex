using MacroRegime.Domain.Common;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Data;

public sealed record MacroObservation
{
    public MacroObservation(
        string seriesCode,
        string name,
        EconomicDimension dimension,
        ObservationDate observationDate,
        PublicationDate publicationDate,
        DateOnly? vintageDate,
        decimal value,
        string source,
        string unit)
    {
        if (string.IsNullOrWhiteSpace(seriesCode))
        {
            throw new ArgumentException("Macro series code is required.", nameof(seriesCode));
        }

        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Macro observation name is required.", nameof(name));
        }

        SeriesCode = seriesCode.Trim();
        Name = name.Trim();
        Dimension = dimension;
        ObservationDate = observationDate;
        PublicationDate = publicationDate;
        VintageDate = vintageDate;
        Value = value;
        Source = source?.Trim() ?? string.Empty;
        Unit = unit?.Trim() ?? string.Empty;
    }

    public string SeriesCode { get; }

    public string Name { get; }

    public EconomicDimension Dimension { get; }

    public ObservationDate ObservationDate { get; }

    public PublicationDate PublicationDate { get; }

    public DateOnly? VintageDate { get; }

    public decimal Value { get; }

    public string Source { get; }

    public string Unit { get; }
}
