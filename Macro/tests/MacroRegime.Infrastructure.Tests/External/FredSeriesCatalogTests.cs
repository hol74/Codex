using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class FredSeriesCatalogTests
{
    [Fact]
    public void Baseline_ContainsSixSeries()
    {
        var codes = FredSeriesCatalog.BaselineSeriesCodes;
        Assert.Equal(new[] { "INDPRO_YOY", "SAHM", "T10YIE", "VIX", "YC_10Y2Y", "HY_OAS" }, codes);
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
    public void Resolve_ReturnsAllSix_ForBaselineCodes()
    {
        foreach (var code in FredSeriesCatalog.BaselineSeriesCodes)
        {
            var meta = FredSeriesCatalog.Resolve(code);
            Assert.Equal(code, meta.SeriesCode);
        }
    }
}
