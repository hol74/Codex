using MacroRegime.Domain.Common;

namespace MacroRegime.Domain.Tests.Common;

public sealed class NormalizedScoreTests
{
    [Theory]
    [InlineData(0)]
    [InlineData(0.5)]
    [InlineData(1)]
    public void Constructor_AllowsValuesBetweenZeroAndOne(double value)
    {
        var score = new NormalizedScore((decimal)value);

        Assert.Equal((decimal)value, score.Value);
    }

    [Theory]
    [InlineData(-0.01)]
    [InlineData(1.01)]
    public void Constructor_RejectsValuesOutsideZeroAndOne(double value)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new NormalizedScore((decimal)value));
    }

    [Fact]
    public void Neutral_IsPointFive()
    {
        Assert.Equal(0.5m, NormalizedScore.Neutral.Value);
        Assert.True(NormalizedScore.Neutral.IsNeutral);
    }
}
