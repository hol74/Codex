namespace MacroRegime.Domain.Time;

public readonly record struct ObservationDate
{
    public ObservationDate(DateOnly value)
    {
        if (value == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "Observation date is required.");
        }

        Value = value;
    }

    public DateOnly Value { get; }

    public bool IsNotAfter(PublicationDate publicationDate)
    {
        return Value <= publicationDate.Value;
    }

    public override string ToString()
    {
        return Value.ToString("yyyy-MM-dd");
    }
}
