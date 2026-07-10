using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Tests.Features;

public sealed class FeatureNormalizerTests
{
    [Fact]
    public void Normalize_UsesPercentScale_ForHighYieldSpread()
    {
        var normalizer = new FeatureNormalizer();

        var result = normalizer.Normalize(
            SnapshotWith("HY_OAS", EconomicDimension.Credit, 7.5m),
            FeatureSetWith(new FeatureDefinition(
                "CREDIT_STRESS",
                "Credit stress",
                EconomicDimension.Credit,
                "HY OAS inverse",
                new FeatureWeight(1m),
                FeaturePolarity.HigherIsRiskOff,
                6,
                true)));

        var score = Assert.Single(result.FeatureScores);
        Assert.Equal(0m, score.NormalizedScore.Value);
    }

    [Fact]
    public void Normalize_UsesNeutralScoreAndWarning_WhenFeatureInputsAreMissing()
    {
        var normalizer = new FeatureNormalizer();

        var result = normalizer.Normalize(
            new DataSnapshot(new AsOfDate(new DateOnly(2026, 7, 1)), Array.Empty<MacroObservation>(), Array.Empty<MarketObservation>()),
            FeatureSetWith(new FeatureDefinition(
                "CREDIT_STRESS",
                "Credit stress",
                EconomicDimension.Credit,
                "HY OAS inverse",
                new FeatureWeight(1m),
                FeaturePolarity.HigherIsRiskOff,
                6,
                true)));

        var score = Assert.Single(result.FeatureScores);
        Assert.Equal(NormalizedScore.Neutral, score.NormalizedScore);
        Assert.Contains("CREDIT_STRESS", Assert.Single(result.Warnings));
    }

    private static DataSnapshot SnapshotWith(string code, EconomicDimension dimension, decimal value)
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        return new DataSnapshot(
            asOf,
            new[]
            {
                new MacroObservation(
                    code,
                    code,
                    dimension,
                    new ObservationDate(new DateOnly(2026, 6, 30)),
                    new PublicationDate(asOf.Value),
                    asOf.Value,
                    value,
                    "Fixture",
                    "Percent")
            },
            Array.Empty<MarketObservation>());
    }

    private static FeatureSetVersion FeatureSetWith(params FeatureDefinition[] definitions)
    {
        return new FeatureSetVersion("CRS Baseline", "0.1", definitions);
    }
}
