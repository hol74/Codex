namespace MacroRegime.Domain.Time;

public readonly record struct AsOfDate
{
    public AsOfDate(DateOnly value)
    {
        if (value == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "As-of date is required.");
        }

        Value = value;
    }

    public DateOnly Value { get; }

    public bool CanUse(PublicationDate publicationDate)
    {
        return publicationDate.Value <= Value;
    }

    public bool CanUse(AvailabilityDate availabilityDate)
    {
        return availabilityDate.Value <= Value;
    }

    public override string ToString()
    {
        return Value.ToString("yyyy-MM-dd");
    }
}
