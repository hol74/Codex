using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Tests.Regimes;

public sealed class BaselineRegimeDetectorTests
{
    [Fact]
    public void Detect_ReturnsUncertainTransition_ForNeutralScenario()
    {
        var snapshot = Detect(Scenario(
            industrialProductionYoY: 0m,
            sahm: 0.5m,
            breakeven: 2.25m,
            vix: 26m,
            curve: 0m,
            highYieldSpread: 5m));

        Assert.Equal(RegimeType.UncertainTransition, snapshot.OperationalRegime);
        Assert.True(snapshot.Confidence.Value < 0.55m);
    }

    [Fact]
    public void Detect_ReturnsGoldilocks_ForConstructiveGrowthLowStressScenario()
    {
        var snapshot = Detect(Scenario(
            industrialProductionYoY: 5m,
            sahm: 0.05m,
            breakeven: 2.0m,
            vix: 14m,
            curve: 0.5m,
            highYieldSpread: 3m));

        Assert.Equal(RegimeType.Goldilocks, snapshot.PrimaryRegime);
        Assert.Equal(RegimeType.Goldilocks, snapshot.OperationalRegime);
        Assert.Contains(snapshot.Explanations, explanation => explanation.FeatureCode == "GROWTH_MOM");
    }

    [Fact]
    public void Detect_ReturnsReflation_WhenGrowthRiskAndInflationAreStrong()
    {
        var snapshot = Detect(Scenario(
            industrialProductionYoY: 5m,
            sahm: 0.1m,
            breakeven: 3.0m,
            vix: 16m,
            curve: -0.4m,
            highYieldSpread: 3.5m));

        Assert.Equal(RegimeType.Reflation, snapshot.PrimaryRegime);
        Assert.Contains(snapshot.Explanations, explanation => explanation.Kind == MacroRegime.Domain.Explanations.RegimeExplanationKind.ContrarySignal);
    }

    [Fact]
    public void Detect_ReturnsStagflation_WhenGrowthIsWeakAndInflationCreditStressAreHigh()
    {
        var snapshot = Detect(Scenario(
            industrialProductionYoY: -5m,
            sahm: 0.8m,
            breakeven: 3.2m,
            vix: 24m,
            curve: -0.5m,
            highYieldSpread: 6.5m));

        Assert.Equal(RegimeType.Stagflation, snapshot.PrimaryRegime);
        Assert.Contains(snapshot.Explanations, explanation => explanation.FeatureCode == "INFL_PRESS");
    }

    [Fact]
    public void Detect_ReturnsLateCycleOverheating_WhenGrowthAndInflationAreStrongAndCurveIsInverted()
    {
        var snapshot = Detect(Scenario(
            industrialProductionYoY: 6m,
            sahm: 0.0m,
            breakeven: 3.4m,
            vix: 32m,
            curve: -1.0m,
            highYieldSpread: 6.5m));

        Assert.Equal(RegimeType.LateCycleOverheating, snapshot.PrimaryRegime);
    }

    [Fact]
    public void Detect_ReturnsDeflationBust_WhenGrowthInflationRiskAndCreditAreWeak()
    {
        var snapshot = Detect(Scenario(
            industrialProductionYoY: -6m,
            sahm: 1.0m,
            breakeven: 1.1m,
            vix: 38m,
            curve: -0.5m,
            highYieldSpread: 8m));

        Assert.Equal(RegimeType.DeflationBust, snapshot.PrimaryRegime);
        Assert.Equal(RegimeType.DeflationBust, snapshot.OperationalRegime);
    }

    [Fact]
    public void Detect_SetsOperationalRegimeToUncertainTransition_WhenSignalsDiverge()
    {
        var snapshot = Detect(Scenario(
            industrialProductionYoY: 6m,
            sahm: 0.0m,
            breakeven: 3.2m,
            vix: 35m,
            curve: 0.2m,
            highYieldSpread: 7m));

        Assert.Equal(RegimeType.UncertainTransition, snapshot.OperationalRegime);
        Assert.Contains(snapshot.Warnings, warning => warning.Contains("Divergent macro signals", StringComparison.OrdinalIgnoreCase));
        Assert.Contains(snapshot.Explanations, explanation => explanation.Kind == MacroRegime.Domain.Explanations.RegimeExplanationKind.ContrarySignal);
    }

    [Fact]
    public void Detect_AddsWarningsAndUsesUncertainTransition_WhenDimensionsAreMissing()
    {
        var snapshot = Detect(Scenario(
            industrialProductionYoY: -5m,
            sahm: 0.8m,
            breakeven: 3.2m,
            vix: 24m,
            curve: null,
            highYieldSpread: null));

        Assert.Equal(RegimeType.UncertainTransition, snapshot.OperationalRegime);
        Assert.Contains(snapshot.Warnings, warning => warning.Contains("MONETARY_COND", StringComparison.OrdinalIgnoreCase));
        Assert.Contains(snapshot.Warnings, warning => warning.Contains("CREDIT_STRESS", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Detect_V12ArchetypeProfile_ConfirmsExactGoldilocksArchetype()
    {
        var observations = new Dictionary<string, decimal>
        {
            ["INDPRO_YOY"] = 3m,
            ["SAHM"] = 0.2m,
            ["T10YIE"] = 2.1m,
            ["CPI_YOY"] = 3m,
            ["CPI_YOY_3M_CHANGE"] = -0.2m,
            ["VIX"] = 17.6m,
            ["YC_10Y2Y"] = 1m,
            ["YC_10Y2Y_3M_CHANGE"] = 0.375m,
            ["HY_OAS"] = 1.6m
        };

        var snapshot = new BaselineRegimeDetector().Detect(
            CreateSnapshot(observations),
            CreateFeatureSetVersion("1.2-candidate"),
            CreateModelVersion(scoringProfile: 12m));

        Assert.Equal(RegimeType.Goldilocks, snapshot.PrimaryRegime);
        Assert.Equal(RegimeType.Goldilocks, snapshot.OperationalRegime);
        Assert.True(snapshot.Confidence.Value > 0.9m);
    }

    [Fact]
    public void Detect_V14GeometricProfile_ConfirmsTranslatedGoldilocksArchetype()
    {
        var observations = new Dictionary<string, decimal>
        {
            ["INDPRO_YOY"] = 3m,
            ["SAHM"] = 0.2m,
            ["T10YIE"] = 2.1m,
            ["CPI_YOY"] = 3m,
            ["CPI_YOY_3M_CHANGE"] = -0.2m,
            ["VIX"] = 17.6m,
            ["YC_10Y2Y"] = 1m,
            ["YC_10Y2Y_3M_CHANGE"] = 0.375m,
            ["HY_OAS"] = 1.6m
        };

        var snapshot = new BaselineRegimeDetector().Detect(
            CreateSnapshot(observations),
            CreateFeatureSetVersion("1.4-candidate"),
            CreateModelVersion(scoringProfile: 14m));

        Assert.Equal(RegimeType.Goldilocks, snapshot.PrimaryRegime);
        Assert.Equal(RegimeType.Goldilocks, snapshot.OperationalRegime);
        Assert.True(snapshot.Confidence.Value > 0.95m);
    }

    [Fact]
    public void Detect_V14TranslatesDivergentRiskThresholdToSameVixLevel()
    {
        var observations = new Dictionary<string, decimal>
        {
            ["INDPRO_YOY"] = 3m,
            ["SAHM"] = 0.2m,
            ["T10YIE"] = 2.7m,
            ["CPI_YOY"] = 5m,
            ["CPI_YOY_3M_CHANGE"] = 0.6m,
            ["VIX"] = 26m,
            ["YC_10Y2Y"] = 1m,
            ["YC_10Y2Y_3M_CHANGE"] = 0.375m,
            ["HY_OAS"] = 1.6m
        };
        var detector = new BaselineRegimeDetector();

        var v13 = detector.Detect(
            CreateSnapshot(observations),
            CreateFeatureSetVersion("1.3-candidate"),
            CreateModelVersion(scoringProfile: 12m));
        var v14 = detector.Detect(
            CreateSnapshot(observations),
            CreateFeatureSetVersion("1.4-candidate"),
            CreateModelVersion(scoringProfile: 14m));

        Assert.Contains(v13.Warnings, warning => warning.Contains("Divergent macro signals"));
        Assert.DoesNotContain(v14.Warnings, warning => warning.Contains("Divergent macro signals"));
    }

    private static RegimeSnapshot Detect(IReadOnlyDictionary<string, decimal> observations)
    {
        return new BaselineRegimeDetector().Detect(CreateSnapshot(observations), CreateFeatureSetVersion(), CreateModelVersion());
    }

    private static IReadOnlyDictionary<string, decimal> Scenario(
        decimal industrialProductionYoY,
        decimal sahm,
        decimal breakeven,
        decimal vix,
        decimal? curve,
        decimal? highYieldSpread)
    {
        var values = new Dictionary<string, decimal>
        {
            ["INDPRO_YOY"] = industrialProductionYoY,
            ["SAHM"] = sahm,
            ["T10YIE"] = breakeven,
            ["VIX"] = vix
        };

        if (curve.HasValue)
        {
            values["YC_10Y2Y"] = curve.Value;
        }

        if (highYieldSpread.HasValue)
        {
            values["HY_OAS"] = highYieldSpread.Value;
        }

        return values;
    }

    private static DataSnapshot CreateSnapshot(IReadOnlyDictionary<string, decimal> observations)
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var observationDate = new ObservationDate(new DateOnly(2026, 6, 30));
        var publicationDate = new PublicationDate(new DateOnly(2026, 7, 1));

        return new DataSnapshot(
            asOfDate,
            observations.Select(observation => new MacroObservation(
                observation.Key,
                observation.Key,
                DimensionFor(observation.Key),
                observationDate,
                publicationDate,
                publicationDate.Value,
                observation.Value,
                "Fixture",
                "Index")),
            Array.Empty<MarketObservation>());
    }

    private static FeatureSetVersion CreateFeatureSetVersion(string version = "0.1")
    {
        return new FeatureSetVersion(
            "CRS Baseline",
            version,
            new[]
            {
                Feature("GROWTH_MOM", "Growth momentum", EconomicDimension.Growth, FeaturePolarity.HigherIsRiskOn),
                Feature("INFL_PRESS", "Inflation pressure", EconomicDimension.Inflation, FeaturePolarity.HigherIsRiskOff),
                Feature("RISK_APPETITE", "Risk appetite", EconomicDimension.Risk, FeaturePolarity.HigherIsRiskOn),
                Feature("MONETARY_COND", "Monetary conditions", EconomicDimension.Monetary, FeaturePolarity.HigherIsRiskOn),
                Feature("CREDIT_STRESS", "Credit stress", EconomicDimension.Credit, FeaturePolarity.HigherIsRiskOff)
            });
    }

    private static FeatureDefinition Feature(string code, string name, EconomicDimension dimension, FeaturePolarity polarity)
    {
        return new FeatureDefinition(
            code,
            name,
            dimension,
            "Baseline v0.1 formula",
            new FeatureWeight(1m),
            polarity,
            6,
            true);
    }

    private static ModelVersion CreateModelVersion(decimal? scoringProfile = null)
    {
        var parameters = new Dictionary<string, decimal>
        {
            ["confirmation_threshold"] = 0.55m
        };
        if (scoringProfile.HasValue)
        {
            parameters["scoring_profile"] = scoringProfile.Value;
            parameters["confidence_fit_weight"] = scoringProfile == 14m ? 0.75m : 0.55m;
            parameters["confidence_margin_weight"] = scoringProfile == 14m ? 0.25m : 1.5m;
        }

        return new ModelVersion(
            "CRS Rule-Based Engine",
            "0.1",
            ModelRole.Baseline,
            parameters,
            new DateOnly(2026, 7, 1),
            "Baseline model");
    }

    private static EconomicDimension DimensionFor(string code)
    {
        return code switch
        {
            "INDPRO_YOY" => EconomicDimension.Growth,
            "SAHM" => EconomicDimension.Growth,
            "T10YIE" => EconomicDimension.Inflation,
            "CPI_YOY" => EconomicDimension.Inflation,
            "CPI_YOY_3M_CHANGE" => EconomicDimension.Inflation,
            "VIX" => EconomicDimension.Risk,
            "YC_10Y2Y" => EconomicDimension.Monetary,
            "YC_10Y2Y_3M_CHANGE" => EconomicDimension.Monetary,
            "HY_OAS" => EconomicDimension.Credit,
            _ => EconomicDimension.Sentiment
        };
    }
}
