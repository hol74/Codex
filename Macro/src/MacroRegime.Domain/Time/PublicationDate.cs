namespace MacroRegime.Domain.Time;

public readonly record struct PublicationDate
{
    public PublicationDate(DateOnly value)
    {
        if (value == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "Publication date is required.");
        }

        Value = value;
    }

    public DateOnly Value { get; }

    public bool IsAvailableAt(AsOfDate asOfDate)
    {
        return Value <= asOfDate.Value;
    }

    public override string ToString()
    {
        return Value.ToString("yyyy-MM-dd");
    }
}
