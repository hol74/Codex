using MacroRegime.Domain.Common;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Domain.Tests.Regimes;

public sealed class RegimeProbabilityTests
{
    [Fact]
    public void Constructor_AcceptsValidProbabilityAndRank()
    {
        var probability = new RegimeProbability(RegimeType.Goldilocks, new Probability(0.42m), 1);

        Assert.Equal(RegimeType.Goldilocks, probability.Regime);
        Assert.Equal(0.42m, probability.Probability.Value);
        Assert.Equal(1, probability.Rank);
    }

    [Fact]
    public void Constructor_RejectsRankLessThanOne()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new RegimeProbability(RegimeType.Goldilocks, new Probability(0.42m), 0));
    }

    [Theory]
    [InlineData(-0.01)]
    [InlineData(1.01)]
    public void Constructor_RejectsInvalidProbability(double value)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new RegimeProbability(RegimeType.Goldilocks, new Probability((decimal)value), 1));
    }
}
