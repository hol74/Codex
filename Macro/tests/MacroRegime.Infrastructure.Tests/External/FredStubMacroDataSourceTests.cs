using MacroRegime.Application.External;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class FredStubMacroDataSourceTests
{
    private static readonly AsOfDate AsOf = new(new DateOnly(2026, 7, 1));

    [Fact]
    public async Task FetchAsync_ReturnsOneObservationPerSeries_ForBaselineSet()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        Assert.Equal(7, result.Count);
        Assert.Equal(FredSeriesCatalog.BaselineSeriesCodes, result.Select(o => o.SeriesCode).ToArray());
    }

    [Fact]
    public async Task FetchAsync_IsDeterministic_SameAsOfSameValues()
    {
        var source = new FredStubMacroDataSource();
        var first = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        var second = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        Assert.Equal(first, second);
    }

    [Fact]
    public async Task FetchAsync_PublicationDate_EqualsAsOf()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        Assert.All(result, o => Assert.Equal(AsOf.Value, o.PublicationDate));
    }

    [Fact]
    public async Task FetchAsync_VintageDate_EqualsAsOf_Flat()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        Assert.All(result, o => Assert.Equal(AsOf.Value, o.VintageDate));
    }

    [Fact]
    public async Task FetchAsync_MonthlySeries_ObservationDate_IsLastDayOfPreviousMonth()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "INDPRO_YOY" })));
        var industrialProduction = Assert.Single(result);
        Assert.Equal(new DateOnly(2026, 6, 30), industrialProduction.ObservationDate);
    }

    [Fact]
    public async Task FetchAsync_DailySeries_ObservationDate_EqualsAsOf()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "VIX" })));
        var vix = Assert.Single(result);
        Assert.Equal(AsOf.Value, vix.ObservationDate);
    }

    [Fact]
    public async Task FetchAsync_ReturnsOnlyRequestedSeries_WhenSubsetRequested()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "VIX", "SAHM" })));
        Assert.Equal(2, result.Count);
        Assert.Contains(result, o => o.SeriesCode == "VIX");
        Assert.Contains(result, o => o.SeriesCode == "SAHM");
    }

    [Fact]
    public async Task FetchAsync_Throws_OnUnknownSeriesCode()
    {
        var source = new FredStubMacroDataSource();
        await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "UNKNOWN" }))));
    }
}
