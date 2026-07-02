using MacroRegime.Domain.Common;

namespace MacroRegime.Domain.Tests.Common;

public sealed class FeatureWeightTests
{
    [Fact]
    public void Constructor_AllowsZero()
    {
        var weight = new FeatureWeight(0m);

        Assert.Equal(0m, weight.Value);
    }

    [Fact]
    public void Constructor_AllowsPositiveValue()
    {
        var weight = new FeatureWeight(0.25m);

        Assert.Equal(0.25m, weight.Value);
    }

    [Fact]
    public void Constructor_RejectsNegativeValue()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new FeatureWeight(-0.01m));
    }
}
