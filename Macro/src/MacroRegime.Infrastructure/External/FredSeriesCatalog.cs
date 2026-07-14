namespace MacroRegime.Infrastructure.External;

public sealed record FredSeriesMetadata(
    string SeriesCode,
    string FredSeriesId,
    string Name,
    string Dimension,
    string Unit,
    string Frequency,
    decimal BaseValue,
    decimal Amplitude,
    string? FredUnits = null);

public static class FredSeriesCatalog
{
    public static IReadOnlyList<string> BaselineSeriesCodes { get; } = new[]
    {
        "INDPRO_YOY", "SAHM", "CPI_YOY", "T10YIE", "VIX", "YC_10Y2Y", "HY_OAS"
    };

    public static IReadOnlyList<string> HistoricalDerivedSeriesCodes { get; } = new[]
    {
        "CPI_YOY_3M_CHANGE", "YC_10Y2Y_3M_CHANGE"
    };

    public static IReadOnlyList<string> HistoricalIntramonthSourceSeriesCodes { get; } = new[]
    {
        "SOFR", "EFFR"
    };

    public static IReadOnlyList<string> HistoricalIntramonthDerivedSeriesCodes { get; } = new[]
    {
        "VIX_MONTHLY_MAX",
        "SOFR_EFFR_MONTHLY_MAX",
        "SPY_MONTHLY_MAX_DRAWDOWN",
        "HYG_MONTHLY_MAX_DRAWDOWN"
    };

    public static IReadOnlyList<string> HistoricalSourceSeriesCodes { get; } =
        BaselineSeriesCodes.Concat(HistoricalIntramonthSourceSeriesCodes).ToArray();

    public static IReadOnlyList<string> HistoricalSnapshotSeriesCodes { get; } =
        BaselineSeriesCodes
            .Concat(HistoricalDerivedSeriesCodes)
            .Concat(HistoricalIntramonthDerivedSeriesCodes)
            .ToArray();

    private static readonly IReadOnlyDictionary<string, FredSeriesMetadata> Entries =
        new Dictionary<string, FredSeriesMetadata>(StringComparer.OrdinalIgnoreCase)
        {
            ["INDPRO_YOY"] = new("INDPRO_YOY", "INDPRO", "Industrial production YoY", "Growth", "Percent change", "monthly", 2.0m, 3.0m, "pc1"),
            ["SAHM"] = new("SAHM", "SAHMREALTIME", "Sahm rule recession indicator", "Growth", "Index", "monthly", 0.05m, 0.10m),
            ["CPI_YOY"] = new("CPI_YOY", "CPIAUCSL", "Consumer price index YoY", "Inflation", "Percent change", "monthly", 2.0m, 1.5m, "pc1"),
            ["T10YIE"] = new("T10YIE", "T10YIE", "10-year breakeven inflation", "Inflation", "Percent", "daily", 2.0m, 0.5m),
            ["VIX"] = new("VIX", "VIXCLS", "CBOE volatility index", "Risk", "Index", "daily", 18.0m, 5.0m),
            ["YC_10Y2Y"] = new("YC_10Y2Y", "T10Y2Y", "10-year minus 2-year Treasury slope", "Monetary", "Percentage points", "daily", 0.0m, 0.5m),
            ["HY_OAS"] = new("HY_OAS", "BAMLH0A0HYM2", "High-yield option-adjusted spread", "Credit", "Percent", "daily", 3.0m, 0.8m),
            ["CPI_YOY_3M_CHANGE"] = new("CPI_YOY_3M_CHANGE", "DERIVED:CPI_YOY", "CPI YoY three-month change", "Inflation", "Percentage points", "derived", 0.0m, 0.5m),
            ["YC_10Y2Y_3M_CHANGE"] = new("YC_10Y2Y_3M_CHANGE", "DERIVED:YC_10Y2Y", "10Y-2Y curve three-month change", "Monetary", "Percentage points", "derived", 0.0m, 0.5m),
            ["SOFR"] = new("SOFR", "SOFR", "Secured overnight financing rate", "Monetary", "Percent", "daily", 2.0m, 1.0m),
            ["EFFR"] = new("EFFR", "EFFR", "Effective federal funds rate", "Monetary", "Percent", "daily", 2.0m, 1.0m),
            ["VIX_MONTHLY_MAX"] = new("VIX_MONTHLY_MAX", "DERIVED:FRED:VIX", "Maximum intramonth VIX", "Risk", "Index", "derived", 18.0m, 8.0m),
            ["SOFR_EFFR_MONTHLY_MAX"] = new("SOFR_EFFR_MONTHLY_MAX", "DERIVED:FRED:SOFR-EFFR", "Maximum intramonth SOFR minus EFFR spread", "Monetary", "Basis points", "derived", 0.0m, 25.0m),
            ["SPY_MONTHLY_MAX_DRAWDOWN"] = new("SPY_MONTHLY_MAX_DRAWDOWN", "DERIVED:MARKET:SPY", "Maximum intramonth SPY drawdown", "Risk", "Percent", "derived", 0.0m, 5.0m),
            ["HYG_MONTHLY_MAX_DRAWDOWN"] = new("HYG_MONTHLY_MAX_DRAWDOWN", "DERIVED:MARKET:HYG", "Maximum intramonth HYG drawdown", "Credit", "Percent", "derived", 0.0m, 3.0m),
        };

    public static FredSeriesMetadata Resolve(string seriesCode)
    {
        return Entries.TryGetValue(seriesCode, out var meta)
            ? meta
            : throw new KeyNotFoundException($"Unknown FRED series code '{seriesCode}'.");
    }
}
