namespace MacroRegime.Application.Regimes;

public sealed record CalculateRegimeCommand
{
    public CalculateRegimeCommand(DateOnly asOfDate)
    {
        if (asOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "As-of date is required.");
        }

        AsOfDate = asOfDate;
    }

    public DateOnly AsOfDate { get; }
}
