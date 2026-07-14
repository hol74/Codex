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

    [Fact]
    public void Normalize_V1UsesBaaProxyScaleWithoutDemoSaturation()
    {
        var normalizer = new FeatureNormalizer();

        var result = normalizer.Normalize(
            SnapshotWith("HY_OAS", EconomicDimension.Credit, 2.5m),
            FeatureSetWith("1.0-candidate", new FeatureDefinition(
                "CREDIT_STRESS",
                "Credit conditions",
                EconomicDimension.Credit,
                "BAA10Y inverse",
                new FeatureWeight(1m),
                FeaturePolarity.HigherIsRiskOff,
                6,
                true)));

        var score = Assert.Single(result.FeatureScores);
        Assert.Equal(0.5m, score.NormalizedScore.Value);
        Assert.Contains("BAA10Y", score.Interpretation);
    }

    [Theory]
    [InlineData(-1.5, 0.0)]
    [InlineData(0.5, 1.0)]
    [InlineData(2.5, 0.0)]
    public void Normalize_V1PenalizesCurveInversionAndExtremeSteepening(double curve, double expected)
    {
        var normalizer = new FeatureNormalizer();

        var result = normalizer.Normalize(
            SnapshotWith("YC_10Y2Y", EconomicDimension.Monetary, (decimal)curve),
            FeatureSetWith("1.0-candidate", new FeatureDefinition(
                "MONETARY_COND",
                "Curve conditions",
                EconomicDimension.Monetary,
                "Centered curve",
                new FeatureWeight(1m),
                FeaturePolarity.HigherIsRiskOn,
                6,
                true)));

        Assert.Equal((decimal)expected, Assert.Single(result.FeatureScores).NormalizedScore.Value);
    }

    [Fact]
    public void Normalize_V1CentersInflationPressureAtTwoPointTwoFivePercent()
    {
        var normalizer = new FeatureNormalizer();

        var result = normalizer.Normalize(
            SnapshotWith("T10YIE", EconomicDimension.Inflation, 2.25m),
            FeatureSetWith("1.0-candidate", new FeatureDefinition(
                "INFL_PRESS",
                "Inflation pressure",
                EconomicDimension.Inflation,
                "Breakeven v1",
                new FeatureWeight(1m),
                FeaturePolarity.HigherIsRiskOff,
                6,
                true)));

        Assert.Equal(0.5m, Assert.Single(result.FeatureScores).NormalizedScore.Value);
    }

    [Fact]
    public void Normalize_V11CombinesBreakevenRealizedInflationAndMomentum()
    {
        var normalizer = new FeatureNormalizer();

        var result = normalizer.Normalize(
            SnapshotWith(
                ("T10YIE", EconomicDimension.Inflation, 2.25m),
                ("CPI_YOY", EconomicDimension.Inflation, 4m),
                ("CPI_YOY_3M_CHANGE", EconomicDimension.Inflation, 1m)),
            FeatureSetWith("1.1-candidate", new FeatureDefinition(
                "INFL_PRESS", "Inflation pressure", EconomicDimension.Inflation, "Temporal inflation",
                new FeatureWeight(1m), FeaturePolarity.HigherIsRiskOff, 6, true)));

        var score = Assert.Single(result.FeatureScores);
        Assert.Equal(0.65m, score.NormalizedScore.Value);
        Assert.Equal(4m, score.RawValue);
        Assert.Contains("point-in-time CPI YoY", score.Interpretation);
    }

    [Theory]
    [InlineData(0.0, 1.0)]
    [InlineData(1.5, 0.7)]
    public void Normalize_V11PenalizesRapidCurveChange(double change, double expected)
    {
        var normalizer = new FeatureNormalizer();

        var result = normalizer.Normalize(
            SnapshotWith(
                ("YC_10Y2Y", EconomicDimension.Monetary, 0.5m),
                ("YC_10Y2Y_3M_CHANGE", EconomicDimension.Monetary, (decimal)change)),
            FeatureSetWith("1.1-candidate", new FeatureDefinition(
                "MONETARY_COND", "Curve conditions", EconomicDimension.Monetary, "Temporal curve",
                new FeatureWeight(1m), FeaturePolarity.HigherIsRiskOn, 6, true)));

        Assert.Equal((decimal)expected, Assert.Single(result.FeatureScores).NormalizedScore.Value);
    }

    [Fact]
    public void Normalize_V13UsesContinuousLogisticVixMappingWithoutChangingV12()
    {
        var normalizer = new FeatureNormalizer();
        var definition = new FeatureDefinition(
            "RISK_APPETITE", "Risk appetite", EconomicDimension.Risk, "VIX inverse",
            new FeatureWeight(1m), FeaturePolarity.HigherIsRiskOn, 6, true);

        var calmV13 = Assert.Single(normalizer.Normalize(
            SnapshotWith("VIX", EconomicDimension.Risk, 12m),
            FeatureSetWith("1.3-candidate", definition)).FeatureScores);
        var neutralV13 = Assert.Single(normalizer.Normalize(
            SnapshotWith("VIX", EconomicDimension.Risk, 20m),
            FeatureSetWith("1.3-candidate", definition)).FeatureScores);
        var stressedV13 = Assert.Single(normalizer.Normalize(
            SnapshotWith("VIX", EconomicDimension.Risk, 40m),
            FeatureSetWith("1.3-candidate", definition)).FeatureScores);
        var calmV12 = Assert.Single(normalizer.Normalize(
            SnapshotWith("VIX", EconomicDimension.Risk, 12m),
            FeatureSetWith("1.2-candidate", definition)).FeatureScores);

        Assert.InRange(calmV13.NormalizedScore.Value, 0.75m, 0.77m);
        Assert.Equal(0.5m, neutralV13.NormalizedScore.Value);
        Assert.InRange(stressedV13.NormalizedScore.Value, 0.05m, 0.06m);
        Assert.Equal(1m, calmV12.NormalizedScore.Value);
        Assert.Contains("inverse logistic", calmV13.Interpretation);
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

    private static DataSnapshot SnapshotWith(params (string Code, EconomicDimension Dimension, decimal Value)[] values)
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        return new DataSnapshot(
            asOf,
            values.Select(item => new MacroObservation(
                item.Code,
                item.Code,
                item.Dimension,
                new ObservationDate(new DateOnly(2026, 6, 30)),
                new PublicationDate(asOf.Value),
                asOf.Value,
                item.Value,
                "Fixture",
                "Index")),
            Array.Empty<MarketObservation>());
    }

    private static FeatureSetVersion FeatureSetWith(params FeatureDefinition[] definitions)
    {
        return FeatureSetWith("0.1", definitions);
    }

    private static FeatureSetVersion FeatureSetWith(string version, params FeatureDefinition[] definitions)
    {
        return new FeatureSetVersion("CRS Baseline", version, definitions);
    }
}
