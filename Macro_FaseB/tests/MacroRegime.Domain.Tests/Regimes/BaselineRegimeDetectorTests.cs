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
            pmi: 50m,
            sahm: 0.5m,
            breakeven: 2.25m,
            vix: 26m,
            curve: 0m,
            highYieldSpread: 500m));

        Assert.Equal(RegimeType.UncertainTransition, snapshot.OperationalRegime);
        Assert.True(snapshot.Confidence.Value < 0.55m);
    }

    [Fact]
    public void Detect_ReturnsGoldilocks_ForConstructiveGrowthLowStressScenario()
    {
        var snapshot = Detect(Scenario(
            pmi: 55m,
            sahm: 0.05m,
            breakeven: 2.0m,
            vix: 14m,
            curve: 0.5m,
            highYieldSpread: 300m));

        Assert.Equal(RegimeType.Goldilocks, snapshot.PrimaryRegime);
        Assert.Equal(RegimeType.Goldilocks, snapshot.OperationalRegime);
        Assert.Contains(snapshot.Explanations, explanation => explanation.FeatureCode == "GROWTH_MOM");
    }

    [Fact]
    public void Detect_ReturnsReflation_WhenGrowthRiskAndInflationAreStrong()
    {
        var snapshot = Detect(Scenario(
            pmi: 55m,
            sahm: 0.1m,
            breakeven: 3.0m,
            vix: 16m,
            curve: -0.4m,
            highYieldSpread: 350m));

        Assert.Equal(RegimeType.Reflation, snapshot.PrimaryRegime);
        Assert.Contains(snapshot.Explanations, explanation => explanation.Kind == MacroRegime.Domain.Explanations.RegimeExplanationKind.ContrarySignal);
    }

    [Fact]
    public void Detect_ReturnsStagflation_WhenGrowthIsWeakAndInflationCreditStressAreHigh()
    {
        var snapshot = Detect(Scenario(
            pmi: 45m,
            sahm: 0.8m,
            breakeven: 3.2m,
            vix: 24m,
            curve: -0.5m,
            highYieldSpread: 650m));

        Assert.Equal(RegimeType.Stagflation, snapshot.PrimaryRegime);
        Assert.Contains(snapshot.Explanations, explanation => explanation.FeatureCode == "INFL_PRESS");
    }

    [Fact]
    public void Detect_ReturnsDeflationBust_WhenGrowthInflationRiskAndCreditAreWeak()
    {
        var snapshot = Detect(Scenario(
            pmi: 43m,
            sahm: 1.0m,
            breakeven: 1.1m,
            vix: 38m,
            curve: -0.5m,
            highYieldSpread: 800m));

        Assert.Equal(RegimeType.DeflationBust, snapshot.PrimaryRegime);
        Assert.Equal(RegimeType.DeflationBust, snapshot.OperationalRegime);
    }

    [Fact]
    public void Detect_SetsOperationalRegimeToUncertainTransition_WhenSignalsDiverge()
    {
        var snapshot = Detect(Scenario(
            pmi: 56m,
            sahm: 0.0m,
            breakeven: 3.2m,
            vix: 35m,
            curve: 0.2m,
            highYieldSpread: 700m));

        Assert.Equal(RegimeType.UncertainTransition, snapshot.OperationalRegime);
        Assert.Contains(snapshot.Warnings, warning => warning.Contains("Divergent macro signals", StringComparison.OrdinalIgnoreCase));
        Assert.Contains(snapshot.Explanations, explanation => explanation.Kind == MacroRegime.Domain.Explanations.RegimeExplanationKind.ContrarySignal);
    }

    [Fact]
    public void Detect_AddsWarningsAndUsesUncertainTransition_WhenDimensionsAreMissing()
    {
        var snapshot = Detect(Scenario(
            pmi: 45m,
            sahm: 0.8m,
            breakeven: 3.2m,
            vix: 24m,
            curve: null,
            highYieldSpread: null));

        Assert.Equal(RegimeType.UncertainTransition, snapshot.OperationalRegime);
        Assert.Contains(snapshot.Warnings, warning => warning.Contains("MONETARY_COND", StringComparison.OrdinalIgnoreCase));
        Assert.Contains(snapshot.Warnings, warning => warning.Contains("CREDIT_STRESS", StringComparison.OrdinalIgnoreCase));
    }

    private static RegimeSnapshot Detect(IReadOnlyDictionary<string, decimal> observations)
    {
        return new BaselineRegimeDetector().Detect(CreateSnapshot(observations), CreateFeatureSetVersion(), CreateModelVersion());
    }

    private static IReadOnlyDictionary<string, decimal> Scenario(
        decimal pmi,
        decimal sahm,
        decimal breakeven,
        decimal vix,
        decimal? curve,
        decimal? highYieldSpread)
    {
        var values = new Dictionary<string, decimal>
        {
            ["ISM_PMI"] = pmi,
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

    private static FeatureSetVersion CreateFeatureSetVersion()
    {
        return new FeatureSetVersion(
            "CRS Baseline",
            "0.1",
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

    private static ModelVersion CreateModelVersion()
    {
        return new ModelVersion(
            "CRS Rule-Based Engine",
            "0.1",
            ModelRole.Baseline,
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m
            },
            new DateOnly(2026, 7, 1),
            "Baseline model");
    }

    private static EconomicDimension DimensionFor(string code)
    {
        return code switch
        {
            "ISM_PMI" => EconomicDimension.Growth,
            "SAHM" => EconomicDimension.Growth,
            "T10YIE" => EconomicDimension.Inflation,
            "VIX" => EconomicDimension.Risk,
            "YC_10Y2Y" => EconomicDimension.Monetary,
            "HY_OAS" => EconomicDimension.Credit,
            _ => EconomicDimension.Sentiment
        };
    }
}
