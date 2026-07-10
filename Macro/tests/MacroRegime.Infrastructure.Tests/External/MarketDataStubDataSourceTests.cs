using MacroRegime.Application.External;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class MarketDataStubDataSourceTests
{
    private static readonly AsOfDate AsOf = new(new DateOnly(2026, 7, 1));

    [Fact]
    public async Task FetchAsync_ReturnsOneObservationPerSymbol_ForBaselineSet()
    {
        var source = new MarketDataStubDataSource();
        var result = await source.FetchAsync(new MarketDataFetchCommand(AsOf, MarketDataSeriesSet.Baseline));
        Assert.Equal(6, result.Count);
        Assert.Equal(MarketDataSeriesCatalog.BaselineSymbols, result.Select(o => o.Symbol).ToArray());
    }

    [Fact]
    public async Task FetchAsync_IsDeterministic_SameAsOfSameValues()
    {
        var source = new MarketDataStubDataSource();
        var first = await source.FetchAsync(new MarketDataFetchCommand(AsOf, MarketDataSeriesSet.Baseline));
        var second = await source.FetchAsync(new MarketDataFetchCommand(AsOf, MarketDataSeriesSet.Baseline));
        Assert.Equal(first, second);
    }

    [Fact]
    public async Task FetchAsync_Throws_OnUnknownSymbol()
    {
        var source = new MarketDataStubDataSource();
        await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            source.FetchAsync(new MarketDataFetchCommand(AsOf, new MarketDataSeriesSet(new[] { "UNKNOWN" }))));
    }
}
