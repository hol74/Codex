using MacroRegime.Domain.Common;
using MacroRegime.Domain.Features;

namespace MacroRegime.Domain.Tests.Features;

public sealed class FeatureDefinitionTests
{
    [Theory]
    [InlineData("")]
    [InlineData(" ")]
    public void Constructor_RejectsEmptyCode(string code)
    {
        Assert.Throws<ArgumentException>(() => new FeatureDefinition(
            code,
            "Growth momentum",
            EconomicDimension.Growth,
            "Industrial production and Sahm rule blend",
            new FeatureWeight(1m),
            FeaturePolarity.HigherIsRiskOn,
            6,
            true));
    }

    [Theory]
    [InlineData("")]
    [InlineData(" ")]
    public void Constructor_RejectsEmptyName(string name)
    {
        Assert.Throws<ArgumentException>(() => new FeatureDefinition(
            "GROWTH_MOM",
            name,
            EconomicDimension.Growth,
            "Industrial production and Sahm rule blend",
            new FeatureWeight(1m),
            FeaturePolarity.HigherIsRiskOn,
            6,
            true));
    }

    [Fact]
    public void Constructor_TrimsCodeAndName()
    {
        var definition = new FeatureDefinition(
            " GROWTH_MOM ",
            " Growth momentum ",
            EconomicDimension.Growth,
            "Industrial production and Sahm rule blend",
            new FeatureWeight(1m),
            FeaturePolarity.HigherIsRiskOn,
            6,
            true);

        Assert.Equal("GROWTH_MOM", definition.Code);
        Assert.Equal("Growth momentum", definition.Name);
    }
}
