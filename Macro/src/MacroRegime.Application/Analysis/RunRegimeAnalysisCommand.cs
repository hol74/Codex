namespace MacroRegime.Application.Analysis;

public sealed record RunRegimeAnalysisCommand
{
    public RunRegimeAnalysisCommand(DateOnly asOfDate, decimal estimatedCostPerTurnover = 0.001m)
    {
        if (asOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "As-of date is required.");
        }

        if (estimatedCostPerTurnover < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(estimatedCostPerTurnover), "Estimated cost per turnover cannot be negative.");
        }

        AsOfDate = asOfDate;
        EstimatedCostPerTurnover = estimatedCostPerTurnover;
    }

    public DateOnly AsOfDate { get; }

    public decimal EstimatedCostPerTurnover { get; }
}
