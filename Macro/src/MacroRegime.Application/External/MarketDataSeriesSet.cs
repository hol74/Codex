namespace MacroRegime.Application.External;

public sealed record MarketDataSeriesSet(IReadOnlyList<string> Symbols)
{
    public static MarketDataSeriesSet Baseline { get; } = new(new[]
    {
        "SPY", "ACWI", "IEF", "GLD", "BIL", "HYG"
    });
}
