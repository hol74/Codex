using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class FredSeriesCatalogTests
{
    [Fact]
    public void Baseline_ContainsSevenSourceSeriesAndTwoDerivedSeries()
    {
        var codes = FredSeriesCatalog.BaselineSeriesCodes;
        Assert.Equal(new[] { "INDPRO_YOY", "SAHM", "CPI_YOY", "T10YIE", "VIX", "YC_10Y2Y", "HY_OAS" }, codes);
        Assert.Equal(new[] { "CPI_YOY_3M_CHANGE", "YC_10Y2Y_3M_CHANGE" }, FredSeriesCatalog.HistoricalDerivedSeriesCodes);
        Assert.Equal(new[] { "SOFR", "EFFR" }, FredSeriesCatalog.HistoricalIntramonthSourceSeriesCodes);
        Assert.Equal(4, FredSeriesCatalog.HistoricalIntramonthDerivedSeriesCodes.Count);
    }

    [Fact]
    public void Resolve_ReturnsMetadata_ForKnownCode()
    {
        var meta = FredSeriesCatalog.Resolve("INDPRO_YOY");
        Assert.Equal("INDPRO", meta.FredSeriesId);
        Assert.Equal("Industrial production YoY", meta.Name);
        Assert.Equal("Growth", meta.Dimension);
        Assert.Equal("Percent change", meta.Unit);
        Assert.Equal("monthly", meta.Frequency);
        Assert.Equal(2.0m, meta.BaseValue);
        Assert.Equal(3.0m, meta.Amplitude);
        Assert.Equal("pc1", meta.FredUnits);
    }

    [Fact]
    public void Resolve_Throws_ForUnknownCode()
    {
        Assert.Throws<KeyNotFoundException>(() => FredSeriesCatalog.Resolve("UNKNOWN"));
    }

    [Fact]
    public void Resolve_ReturnsMetadata_ForAllHistoricalSnapshotCodes()
    {
        foreach (var code in FredSeriesCatalog.HistoricalSnapshotSeriesCodes)
        {
            var meta = FredSeriesCatalog.Resolve(code);
            Assert.Equal(code, meta.SeriesCode);
        }
    }
}
