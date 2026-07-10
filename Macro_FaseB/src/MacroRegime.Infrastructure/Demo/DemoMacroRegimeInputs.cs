using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Demo;

public static class DemoMacroRegimeInputs
{
    public static DataSnapshot CreateGoldilocksDataSnapshot(AsOfDate asOfDate)
    {
        var observationDate = new ObservationDate(asOfDate.Value.AddDays(-1));
        var publicationDate = new PublicationDate(asOfDate.Value);

        return new DataSnapshot(
            asOfDate,
            new[]
            {
                Observation("ISM_PMI", "ISM manufacturing PMI", EconomicDimension.Growth, 55m, observationDate, publicationDate),
                Observation("SAHM", "Sahm rule recession indicator", EconomicDimension.Growth, 0.05m, observationDate, publicationDate),
                Observation("T10YIE", "10-year breakeven inflation", EconomicDimension.Inflation, 2.0m, observationDate, publicationDate),
                Observation("VIX", "CBOE volatility index", EconomicDimension.Risk, 14m, observationDate, publicationDate),
                Observation("YC_10Y2Y", "10-year minus 2-year Treasury slope", EconomicDimension.Monetary, 0.5m, observationDate, publicationDate),
                Observation("HY_OAS", "High-yield option-adjusted spread", EconomicDimension.Credit, 300m, observationDate, publicationDate)
            },
            Array.Empty<MarketObservation>());
    }

    public static FeatureSetVersion CreateFeatureSetVersion()
    {
        return new FeatureSetVersion(
            "CRS Baseline",
            "0.1-demo",
            new[]
            {
                Feature("GROWTH_MOM", "Growth momentum", EconomicDimension.Growth, FeaturePolarity.HigherIsRiskOn),
                Feature("INFL_PRESS", "Inflation pressure", EconomicDimension.Inflation, FeaturePolarity.HigherIsRiskOff),
                Feature("RISK_APPETITE", "Risk appetite", EconomicDimension.Risk, FeaturePolarity.HigherIsRiskOn),
                Feature("MONETARY_COND", "Monetary conditions", EconomicDimension.Monetary, FeaturePolarity.HigherIsRiskOn),
                Feature("CREDIT_STRESS", "Credit stress", EconomicDimension.Credit, FeaturePolarity.HigherIsRiskOff)
            });
    }

    public static ModelVersion CreateModelVersion()
    {
        return new ModelVersion(
            "CRS Rule-Based Engine",
            "0.1-demo",
            ModelRole.Baseline,
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m
            },
            new DateOnly(2026, 7, 1),
            "Deterministic demo model for local macro-regime analysis.");
    }

    public static StrategicAllocationPolicy CreateStrategicAllocationPolicy()
    {
        return new StrategicAllocationPolicy(
            "Balanced Demo IPS",
            new[]
            {
                new AllocationBand(AssetClass.Cash, new AllocationWeight(0.02m), new AllocationWeight(0.05m), new AllocationWeight(0.20m)),
                new AllocationBand(AssetClass.GlobalEquity, new AllocationWeight(0.45m), new AllocationWeight(0.60m), new AllocationWeight(0.75m)),
                new AllocationBand(AssetClass.GovernmentBonds, new AllocationWeight(0.10m), new AllocationWeight(0.25m), new AllocationWeight(0.40m)),
                new AllocationBand(AssetClass.Gold, new AllocationWeight(0.00m), new AllocationWeight(0.10m), new AllocationWeight(0.20m))
            },
            new AllocationWeight(0.25m),
            0.001m);
    }

    public static CurrentPortfolio CreateCurrentPortfolio()
    {
        return new CurrentPortfolio(new[]
        {
            new PortfolioWeight(AssetClass.Cash, new AllocationWeight(0.05m)),
            new PortfolioWeight(AssetClass.GlobalEquity, new AllocationWeight(0.60m)),
            new PortfolioWeight(AssetClass.GovernmentBonds, new AllocationWeight(0.25m)),
            new PortfolioWeight(AssetClass.Gold, new AllocationWeight(0.10m))
        });
    }

    public static IReadOnlyList<RegimeTiltRule> CreateTiltRules()
    {
        return new[]
        {
            new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GlobalEquity, 0.08m, "Constructive growth supports equity tilt."),
            new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.GovernmentBonds, -0.05m, "Duration can be reduced in risk-on regimes."),
            new RegimeTiltRule(RegimeType.Goldilocks, AssetClass.Cash, -0.03m, "Cash drag can be reduced while risk appetite is strong."),
            new RegimeTiltRule(RegimeType.RecessionStress, AssetClass.GlobalEquity, -0.10m, "Recession stress reduces equity risk."),
            new RegimeTiltRule(RegimeType.RecessionStress, AssetClass.GovernmentBonds, 0.08m, "Duration can diversify recession stress."),
            new RegimeTiltRule(RegimeType.RecessionStress, AssetClass.Cash, 0.02m, "Cash buffer supports optionality in stress regimes.")
        };
    }

    private static MacroObservation Observation(
        string code,
        string name,
        EconomicDimension dimension,
        decimal value,
        ObservationDate observationDate,
        PublicationDate publicationDate)
    {
        return new MacroObservation(
            code,
            name,
            dimension,
            observationDate,
            publicationDate,
            publicationDate.Value,
            value,
            "Demo",
            "Index");
    }

    private static FeatureDefinition Feature(string code, string name, EconomicDimension dimension, FeaturePolarity polarity)
    {
        return new FeatureDefinition(
            code,
            name,
            dimension,
            "Deterministic demo feature definition.",
            new FeatureWeight(1m),
            polarity,
            6,
            true);
    }
}
