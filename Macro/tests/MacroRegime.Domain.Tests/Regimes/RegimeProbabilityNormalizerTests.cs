using MacroRegime.Domain.Regimes;

namespace MacroRegime.Domain.Tests.Regimes;

public sealed class RegimeProbabilityNormalizerTests
{
    [Fact]
    public void Normalize_NormalizesRawDistributionAndRanksDescending()
    {
        var normalizer = new RegimeProbabilityNormalizer();

        var probabilities = normalizer.Normalize(new Dictionary<RegimeType, decimal>
        {
            [RegimeType.Goldilocks] = 3m,
            [RegimeType.Reflation] = 1m,
            [RegimeType.Stagflation] = 2m
        });

        Assert.Equal(RegimeType.Goldilocks, probabilities[0].Regime);
        Assert.Equal(0.5m, probabilities[0].Probability.Value);
        Assert.Equal(RegimeType.Stagflation, probabilities[1].Regime);
        Assert.Equal(1m, probabilities.Sum(probability => probability.Probability.Value));
        Assert.Equal(new[] { 1, 2, 3 }, probabilities.Select(probability => probability.Rank));
    }

    [Fact]
    public void Normalize_ReturnsUniformDistribution_WhenRawScoreSumIsZero()
    {
        var normalizer = new RegimeProbabilityNormalizer();

        var probabilities = normalizer.Normalize(new Dictionary<RegimeType, decimal>
        {
            [RegimeType.Goldilocks] = 0m,
            [RegimeType.Reflation] = 0m,
            [RegimeType.Stagflation] = 0m
        });

        Assert.Equal(3, probabilities.Count);
        Assert.Equal(1m, probabilities.Sum(probability => probability.Probability.Value));
        Assert.All(probabilities, probability => Assert.InRange(probability.Probability.Value, 0.3333333333333333333333333333m, 0.3333333333333333333333333334m));
    }

    [Fact]
    public void Normalize_RejectsEmptyDistribution()
    {
        var normalizer = new RegimeProbabilityNormalizer();

        Assert.Throws<ArgumentException>(() => normalizer.Normalize(new Dictionary<RegimeType, decimal>()));
    }

    [Fact]
    public void Normalize_RejectsNegativeRawScores()
    {
        var normalizer = new RegimeProbabilityNormalizer();

        Assert.Throws<ArgumentOutOfRangeException>(() => normalizer.Normalize(new Dictionary<RegimeType, decimal>
        {
            [RegimeType.Goldilocks] = -1m
        }));
    }
}
