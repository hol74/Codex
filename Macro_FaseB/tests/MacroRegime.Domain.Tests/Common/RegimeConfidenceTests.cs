using MacroRegime.Domain.Common;

namespace MacroRegime.Domain.Tests.Common;

public sealed class RegimeConfidenceTests
{
    [Theory]
    [InlineData(0)]
    [InlineData(0.60)]
    [InlineData(1)]
    public void Constructor_AllowsValuesBetweenZeroAndOne(double value)
    {
        var confidence = new RegimeConfidence((decimal)value);

        Assert.Equal((decimal)value, confidence.Value);
    }

    [Theory]
    [InlineData(-0.01)]
    [InlineData(1.01)]
    public void Constructor_RejectsValuesOutsideZeroAndOne(double value)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new RegimeConfidence((decimal)value));
    }
}
