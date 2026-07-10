namespace MacroRegime.Application.External;

public sealed record FredSeriesSet(IReadOnlyList<string> SeriesCodes)
{
    public static FredSeriesSet Baseline { get; } = new(new[]
    {
        "INDPRO_YOY", "SAHM", "T10YIE", "VIX", "YC_10Y2Y", "HY_OAS"
    });
}
