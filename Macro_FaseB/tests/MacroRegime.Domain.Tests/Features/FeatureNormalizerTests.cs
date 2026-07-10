using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Tests.Features;

public sealed class FeatureNormalizerTests
{
    [Fact]
    public void Normalize_UsesNeutralScoreAndWarning_WhenFeatureInputsAreMissing()
    {
        var normalizer = new FeatureNormalizer();

        var result = normalizer.Normalize(
            new DataSnapshot(new AsOfDate(new DateOnly(2026, 7, 1)), Array.Empty<MacroObservation>(), Array.Empty<MarketObservation>()),
            new FeatureSetVersion(
                "CRS Baseline",
                "0.1",
                new[]
                {
                    new FeatureDefinition(
                        "CREDIT_STRESS",
                        "Credit stress",
                        EconomicDimension.Credit,
                        "HY OAS inverse",
                        new FeatureWeight(1m),
                        FeaturePolarity.HigherIsRiskOff,
                        6,
                        true)
                }));

        var score = Assert.Single(result.FeatureScores);
        Assert.Equal(NormalizedScore.Neutral, score.NormalizedScore);
        Assert.Contains("CREDIT_STRESS", Assert.Single(result.Warnings));
    }
}
