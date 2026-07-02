using MacroRegime.Domain.Common;
using MacroRegime.Domain.Features;

namespace MacroRegime.Domain.Tests.Features;

public sealed class FeatureScoreTests
{
    [Fact]
    public void Constructor_AcceptsCoherentInput()
    {
        var score = new FeatureScore(
            "GROWTH_MOM",
            "Growth momentum",
            EconomicDimension.Growth,
            new FeatureWeight(1m),
            52m,
            new NormalizedScore(0.7m),
            0.5m,
            0.1m,
            "Growth is improving.");

        Assert.Equal("GROWTH_MOM", score.FeatureCode);
        Assert.Equal(0.7m, score.NormalizedScore.Value);
    }

    [Theory]
    [InlineData("")]
    [InlineData(" ")]
    public void Constructor_RejectsEmptyFeatureCode(string featureCode)
    {
        Assert.Throws<ArgumentException>(() => new FeatureScore(
            featureCode,
            "Growth momentum",
            EconomicDimension.Growth,
            new FeatureWeight(1m),
            52m,
            new NormalizedScore(0.7m),
            null,
            null,
            string.Empty));
    }

    [Theory]
    [InlineData("")]
    [InlineData(" ")]
    public void Constructor_RejectsEmptyName(string name)
    {
        Assert.Throws<ArgumentException>(() => new FeatureScore(
            "GROWTH_MOM",
            name,
            EconomicDimension.Growth,
            new FeatureWeight(1m),
            52m,
            new NormalizedScore(0.7m),
            null,
            null,
            string.Empty));
    }

    [Fact]
    public void Constructor_RejectsInvalidNormalizedScore()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new FeatureScore(
            "GROWTH_MOM",
            "Growth momentum",
            EconomicDimension.Growth,
            new FeatureWeight(1m),
            52m,
            new NormalizedScore(1.01m),
            null,
            null,
            string.Empty));
    }
}
