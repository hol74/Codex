using MacroRegime.Domain.Common;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;

namespace MacroRegime.Infrastructure.Research;

public static class ResearchMacroRegimeInputs
{
    public static FeatureSetVersion CreateFeatureSetVersion()
    {
        return new FeatureSetVersion(
            "CRS Research Baseline",
            "1.0-candidate",
            new[]
            {
                Feature("GROWTH_MOM", "Growth momentum", EconomicDimension.Growth, FeaturePolarity.HigherIsRiskOn,
                    "Industrial production YoY and Sahm rule composite; unchanged from demo pending longer macro history."),
                Feature("INFL_PRESS", "Inflation pressure", EconomicDimension.Inflation, FeaturePolarity.HigherIsRiskOff,
                    "T10YIE mapped from 1.5% to 3.0%; realized inflation remains an explicit data gap."),
                Feature("RISK_APPETITE", "Risk appetite", EconomicDimension.Risk, FeaturePolarity.HigherIsRiskOn,
                    "Inverse VIX mapping; unchanged from demo."),
                Feature("MONETARY_COND", "Curve conditions", EconomicDimension.Monetary, FeaturePolarity.HigherIsRiskOn,
                    "Non-monotonic 10Y-2Y mapping centered on +0.5%; inversion and extreme steepening are penalized."),
                Feature("CREDIT_STRESS", "Credit conditions", EconomicDimension.Credit, FeaturePolarity.HigherIsRiskOff,
                    "Inverse BAA10Y proxy mapping over 1%-4%; not labeled as high-yield OAS.")
            });
    }

    public static ModelVersion CreateModelVersion()
    {
        return new ModelVersion(
            "CRS Rule-Based Research Candidate",
            "1.0-candidate",
            ModelRole.Baseline,
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m
            },
            new DateOnly(2026, 7, 13),
            "Research-only baseline candidate with corrected feature semantics; not approved for operational allocation.");
    }

    public static FeatureSetVersion CreateFeatureSetVersionV11()
    {
        return new FeatureSetVersion(
            "CRS Research Baseline",
            "1.1-candidate",
            new[]
            {
                Feature("GROWTH_MOM", "Growth momentum", EconomicDimension.Growth, FeaturePolarity.HigherIsRiskOn,
                    "Industrial production YoY and Sahm rule composite; unchanged to isolate temporal inflation and curve signals."),
                Feature("INFL_PRESS", "Inflation pressure", EconomicDimension.Inflation, FeaturePolarity.HigherIsRiskOff,
                    "30% T10YIE, 50% point-in-time CPI YoY and 20% CPI YoY three-month change."),
                Feature("RISK_APPETITE", "Risk appetite", EconomicDimension.Risk, FeaturePolarity.HigherIsRiskOn,
                    "Inverse VIX mapping; unchanged from prior candidates."),
                Feature("MONETARY_COND", "Curve conditions", EconomicDimension.Monetary, FeaturePolarity.HigherIsRiskOn,
                    "70% non-monotonic 10Y-2Y level and 30% three-month change stability."),
                Feature("CREDIT_STRESS", "Credit conditions", EconomicDimension.Credit, FeaturePolarity.HigherIsRiskOff,
                    "Inverse BAA10Y proxy mapping over 1%-4%; unchanged from 1.0-candidate.")
            });
    }

    public static ModelVersion CreateModelVersionV11()
    {
        return new ModelVersion(
            "CRS Rule-Based Research Candidate",
            "1.1-candidate",
            ModelRole.Baseline,
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m
            },
            new DateOnly(2026, 7, 13),
            "Research-only temporal feature candidate; raw regime scores and threshold unchanged from 1.0-candidate.");
    }

    public static FeatureSetVersion CreateFeatureSetVersionV12()
    {
        var prior = CreateFeatureSetVersionV11();
        return new FeatureSetVersion(prior.Name, "1.2-candidate", prior.FeatureDefinitions);
    }

    public static ModelVersion CreateModelVersionV12()
    {
        return new ModelVersion(
            "CRS Archetype Research Candidate",
            "1.2-candidate",
            ModelRole.Baseline,
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m,
                ["scoring_profile"] = 12m,
                ["confidence_fit_weight"] = 0.55m,
                ["confidence_margin_weight"] = 1.5m
            },
            new DateOnly(2026, 7, 13),
            "Research-only preregistered archetype-distance candidate; outer OOS remains sealed until the train-only gate passes.");
    }

    public static FeatureSetVersion CreateFeatureSetVersionV13()
    {
        var prior = CreateFeatureSetVersionV12();
        var definitions = prior.FeatureDefinitions
            .Select(definition => definition.Code == "RISK_APPETITE"
                ? Feature(
                    "RISK_APPETITE",
                    "Risk appetite",
                    EconomicDimension.Risk,
                    FeaturePolarity.HigherIsRiskOn,
                    "Inverse logistic VIX mapping centered at 20 with scale 7; continuous and without hard clipping.")
                : definition)
            .ToArray();
        return new FeatureSetVersion(prior.Name, "1.3-candidate", definitions);
    }

    public static ModelVersion CreateModelVersionV13()
    {
        return new ModelVersion(
            "CRS Archetype Research Candidate",
            "1.3-candidate",
            ModelRole.Baseline,
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m,
                ["scoring_profile"] = 12m,
                ["confidence_fit_weight"] = 0.55m,
                ["confidence_margin_weight"] = 1.5m
            },
            new DateOnly(2026, 7, 13),
            "Research-only preregistered VIX-normalization candidate; scoring and confidence unchanged from 1.2-candidate.");
    }

    public static FeatureSetVersion CreateFeatureSetVersionV14()
    {
        var prior = CreateFeatureSetVersionV13();
        return new FeatureSetVersion(prior.Name, "1.4-candidate", prior.FeatureDefinitions);
    }

    public static ModelVersion CreateModelVersionV14()
    {
        return new ModelVersion(
            "CRS Geometric Archetype Research Candidate",
            "1.4-candidate",
            ModelRole.Baseline,
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m,
                ["scoring_profile"] = 14m,
                ["confidence_fit_weight"] = 0.75m,
                ["confidence_margin_weight"] = 0.25m
            },
            new DateOnly(2026, 7, 13),
            "Research-only preregistered semantic-anchor and geometric-confidence candidate; VIX normalization unchanged from 1.3-candidate.");
    }

    private static FeatureDefinition Feature(
        string code,
        string name,
        EconomicDimension dimension,
        FeaturePolarity polarity,
        string formulaDescription)
    {
        return new FeatureDefinition(
            code,
            name,
            dimension,
            formulaDescription,
            new FeatureWeight(1m),
            polarity,
            6,
            true);
    }
}
