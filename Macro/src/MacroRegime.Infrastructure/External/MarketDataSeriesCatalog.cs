namespace MacroRegime.Infrastructure.External;

public sealed record MarketDataSeriesMetadata(
    string Symbol,
    string ProviderSymbol,
    string Name,
    string Dimension,
    string Unit,
    string ProxyRole,
    decimal BaseValue,
    decimal Amplitude);

public static class MarketDataSeriesCatalog
{
    public static IReadOnlyList<string> BaselineSymbols { get; } = new[]
    {
        "SPY", "ACWI", "IEF", "GLD", "BIL", "HYG"
    };

    private static readonly IReadOnlyDictionary<string, MarketDataSeriesMetadata> Entries =
        new Dictionary<string, MarketDataSeriesMetadata>(StringComparer.OrdinalIgnoreCase)
        {
            ["SPY"] = new("SPY", "SPY", "SPDR S&P 500 ETF Trust", "Risk", "Adjusted close", "US equity proxy", 500m, 80m),
            ["ACWI"] = new("ACWI", "ACWI", "iShares MSCI ACWI ETF", "Risk", "Adjusted close", "Global equity proxy", 120m, 20m),
            ["IEF"] = new("IEF", "IEF", "iShares 7-10 Year Treasury Bond ETF", "Monetary", "Adjusted close", "Government bond proxy", 95m, 8m),
            ["GLD"] = new("GLD", "GLD", "SPDR Gold Shares", "Inflation", "Adjusted close", "Gold proxy", 220m, 35m),
            ["BIL"] = new("BIL", "BIL", "SPDR Bloomberg 1-3 Month T-Bill ETF", "Monetary", "Adjusted close", "Cash proxy", 91m, 2m),
            ["HYG"] = new("HYG", "HYG", "iShares iBoxx High Yield Corporate Bond ETF", "Credit", "Adjusted close", "High-yield credit proxy", 78m, 8m),
        };

    public static MarketDataSeriesMetadata Resolve(string symbol)
    {
        return Entries.TryGetValue(symbol, out var meta)
            ? meta
            : throw new KeyNotFoundException($"Unknown market data symbol '{symbol}'.");
    }
}
