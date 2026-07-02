using MacroRegime.Domain.Common;

namespace MacroRegime.Domain.Tests.Common;

public sealed class ProbabilityTests
{
    [Theory]
    [InlineData(0)]
    [InlineData(0.42)]
    [InlineData(1)]
    public void Constructor_AllowsValuesBetweenZeroAndOne(double value)
    {
        var probability = new Probability((decimal)value);

        Assert.Equal((decimal)value, probability.Value);
    }

    [Theory]
    [InlineData(-0.01)]
    [InlineData(1.01)]
    public void Constructor_RejectsValuesOutsideZeroAndOne(double value)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new Probability((decimal)value));
    }

    [Fact]
    public void Constants_ExposeZeroAndOne()
    {
        Assert.Equal(0m, Probability.Zero.Value);
        Assert.Equal(1m, Probability.One.Value);
    }
}
