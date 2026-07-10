using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class MarketDataSeriesCatalogTests
{
    [Fact]
    public void Baseline_ContainsSixSymbols()
    {
        var symbols = MarketDataSeriesCatalog.BaselineSymbols;
        Assert.Equal(new[] { "SPY", "ACWI", "IEF", "GLD", "BIL", "HYG" }, symbols);
    }

    [Fact]
    public void Resolve_ReturnsMetadata_ForKnownSymbol()
    {
        var meta = MarketDataSeriesCatalog.Resolve("SPY");
        Assert.Equal("SPY", meta.ProviderSymbol);
        Assert.Equal("SPDR S&P 500 ETF Trust", meta.Name);
        Assert.Equal("Risk", meta.Dimension);
        Assert.Equal("Adjusted close", meta.Unit);
        Assert.Equal("US equity proxy", meta.ProxyRole);
    }

    [Fact]
    public void Resolve_Throws_ForUnknownSymbol()
    {
        Assert.Throws<KeyNotFoundException>(() => MarketDataSeriesCatalog.Resolve("UNKNOWN"));
    }
}
