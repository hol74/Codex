using MacroRegime.Domain.Common;
using MacroRegime.Domain.Features;

namespace MacroRegime.Domain.Tests.Features;

public sealed class CompositeScoreCalculatorTests
{
    [Fact]
    public void Calculate_ReturnsWeightedAverage()
    {
        var calculator = new CompositeScoreCalculator();

        var compositeScore = calculator.Calculate(new[]
        {
            CreateScore("GROWTH_MOM", 0.8m, 2m),
            CreateScore("RISK_APPETITE", 0.2m, 1m)
        });

        Assert.Equal(0.6m, compositeScore.Value);
    }

    [Fact]
    public void Calculate_ReturnsNeutralScore_WhenTotalWeightIsZero()
    {
        var calculator = new CompositeScoreCalculator();

        var compositeScore = calculator.Calculate(new[]
        {
            CreateScore("GROWTH_MOM", 0.8m, 0m),
            CreateScore("RISK_APPETITE", 0.2m, 0m)
        });

        Assert.Equal(NormalizedScore.Neutral, compositeScore);
    }

    [Fact]
    public void Calculate_ReturnsNeutralScore_WhenFeatureSetIsEmpty()
    {
        var calculator = new CompositeScoreCalculator();

        var compositeScore = calculator.Calculate(Array.Empty<FeatureScore>());

        Assert.Equal(NormalizedScore.Neutral, compositeScore);
    }

    private static FeatureScore CreateScore(string code, decimal normalizedScore, decimal weight)
    {
        return new FeatureScore(
            code,
            code,
            EconomicDimension.Growth,
            new FeatureWeight(weight),
            normalizedScore,
            new NormalizedScore(normalizedScore),
            null,
            null,
            string.Empty);
    }
}
