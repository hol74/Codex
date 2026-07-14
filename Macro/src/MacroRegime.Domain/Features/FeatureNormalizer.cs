using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;

namespace MacroRegime.Domain.Features;

public sealed class FeatureNormalizer
{
    public FeatureNormalizationResult Normalize(DataSnapshot snapshot, FeatureSetVersion featureSetVersion)
    {
        ArgumentNullException.ThrowIfNull(snapshot);
        ArgumentNullException.ThrowIfNull(featureSetVersion);

        var scores = new List<FeatureScore>();
        var warnings = new List<string>();

        foreach (var definition in featureSetVersion.FeatureDefinitions.Where(definition => definition.IsActive))
        {
            var result = NormalizeFeature(
                snapshot,
                definition,
                UsesResearchV1(featureSetVersion),
                UsesResearchV11(featureSetVersion),
                UsesResearchV13(featureSetVersion));
            if (result.Warning is not null)
            {
                warnings.Add(result.Warning);
            }

            scores.Add(new FeatureScore(
                definition.Code,
                definition.Name,
                definition.Dimension,
                definition.Weight,
                result.RawValue,
                new NormalizedScore(result.Score),
                null,
                null,
                result.Interpretation));
        }

        return new FeatureNormalizationResult(scores, warnings);
    }

    private static FeatureNormalizationResultItem NormalizeFeature(
        DataSnapshot snapshot,
        FeatureDefinition definition,
        bool usesResearchV1,
        bool usesResearchV11,
        bool usesResearchV13)
    {
        return definition.Code.ToUpperInvariant() switch
        {
            "GROWTH_MOM" => NormalizeGrowthMomentum(snapshot, definition),
            "INFL_PRESS" => NormalizeInflationPressure(snapshot, definition, usesResearchV1, usesResearchV11),
            "RISK_APPETITE" => NormalizeRiskAppetite(snapshot, definition, usesResearchV13),
            "MONETARY_COND" => NormalizeMonetaryConditions(snapshot, definition, usesResearchV1, usesResearchV11),
            "CREDIT_STRESS" => NormalizeCreditStress(snapshot, definition, usesResearchV1),
            _ => NormalizeDirectFeature(snapshot, definition)
        };
    }

    private static FeatureNormalizationResultItem NormalizeGrowthMomentum(DataSnapshot snapshot, FeatureDefinition definition)
    {
        var hasIndustrialProduction = snapshot.TryGetValue("INDPRO_YOY", out var industrialProduction);
        var hasSahm = snapshot.TryGetValue("SAHM", out var sahm);

        if (!hasIndustrialProduction && !hasSahm)
        {
            return Missing(definition, "INDPRO_YOY or SAHM");
        }

        var industrialProductionScore = hasIndustrialProduction ? Clamp01((industrialProduction + 5m) / 10m) : 0.5m;
        var sahmScore = hasSahm ? 1m - Clamp01(sahm) : 0.5m;
        var score = (industrialProductionScore + sahmScore) / 2m;

        return new FeatureNormalizationResultItem(score, score, "Growth momentum normalized from industrial production YoY and Sahm rule.", MissingPartial(definition, hasIndustrialProduction, hasSahm, "INDPRO_YOY", "SAHM"));
    }

    private static FeatureNormalizationResultItem NormalizeInflationPressure(
        DataSnapshot snapshot,
        FeatureDefinition definition,
        bool usesResearchV1,
        bool usesResearchV11)
    {
        if (!snapshot.TryGetValue("T10YIE", out var breakeven))
        {
            return Missing(definition, "T10YIE");
        }

        if (usesResearchV11)
        {
            var hasRealized = snapshot.TryGetValue("CPI_YOY", out var realizedInflation);
            var hasMomentum = snapshot.TryGetValue("CPI_YOY_3M_CHANGE", out var inflationMomentum);
            if (!hasRealized || !hasMomentum)
            {
                return Missing(definition, "CPI_YOY and CPI_YOY_3M_CHANGE");
            }

            var breakevenScore = Clamp01((breakeven - 1.5m) / 1.5m);
            var realizedScore = Clamp01((realizedInflation - 1m) / 5m);
            var momentumScore = Clamp01((inflationMomentum + 1m) / 2m);
            var combined = (breakevenScore * 0.3m) + (realizedScore * 0.5m) + (momentumScore * 0.2m);
            return new FeatureNormalizationResultItem(
                realizedInflation,
                combined,
                "Inflation pressure v1.1 combines 10-year breakeven, point-in-time CPI YoY and its three-month change.",
                null);
        }

        var score = usesResearchV1
            ? Clamp01((breakeven - 1.5m) / 1.5m)
            : Clamp01((breakeven - 1m) / 2.5m);
        var interpretation = usesResearchV1
            ? "Inflation pressure v1 normalized from 10-year breakeven over a 1.5%-3.0% range; realized inflation is not yet included."
            : "Inflation pressure normalized from breakeven inflation.";
        return new FeatureNormalizationResultItem(breakeven, score, interpretation, null);
    }

    private static FeatureNormalizationResultItem NormalizeRiskAppetite(
        DataSnapshot snapshot,
        FeatureDefinition definition,
        bool usesResearchV13)
    {
        if (!snapshot.TryGetValue("VIX", out var vix))
        {
            return Missing(definition, "VIX");
        }

        if (usesResearchV13)
        {
            var score = (decimal)(1d / (1d + Math.Exp(((double)vix - 20d) / 7d)));
            return new FeatureNormalizationResultItem(
                vix,
                score,
                "Risk appetite v1.3 uses an inverse logistic VIX mapping centered at 20 with scale 7.",
                null);
        }

        var legacyScore = 1m - Clamp01((vix - 12m) / 28m);
        return new FeatureNormalizationResultItem(vix, legacyScore, "Risk appetite normalized inversely from VIX.", null);
    }

    private static FeatureNormalizationResultItem NormalizeMonetaryConditions(
        DataSnapshot snapshot,
        FeatureDefinition definition,
        bool usesResearchV1,
        bool usesResearchV11)
    {
        if (!snapshot.TryGetValue("YC_10Y2Y", out var curve))
        {
            return Missing(definition, "YC_10Y2Y");
        }

        if (usesResearchV11)
        {
            if (!snapshot.TryGetValue("YC_10Y2Y_3M_CHANGE", out var curveChange))
            {
                return Missing(definition, "YC_10Y2Y_3M_CHANGE");
            }

            var levelScore = 1m - Clamp01(Math.Abs(curve - 0.5m) / 2m);
            var changeStability = 1m - Clamp01(Math.Abs(curveChange) / 1.5m);
            var combined = (levelScore * 0.7m) + (changeStability * 0.3m);
            return new FeatureNormalizationResultItem(
                curve,
                combined,
                "Monetary conditions v1.1 combine curve level with three-month change; inversion and rapid re-steepening are penalized.",
                null);
        }

        var score = usesResearchV1
            ? 1m - Clamp01(Math.Abs(curve - 0.5m) / 2m)
            : Clamp01((curve + 1m) / 2m);
        var interpretation = usesResearchV1
            ? "Monetary conditions v1 score a moderately positive 10Y-2Y slope highest and penalize inversion or extreme steepening."
            : "Monetary conditions normalized from 10Y-2Y curve slope.";
        return new FeatureNormalizationResultItem(curve, score, interpretation, null);
    }

    private static FeatureNormalizationResultItem NormalizeCreditStress(
        DataSnapshot snapshot,
        FeatureDefinition definition,
        bool usesResearchV1)
    {
        if (!snapshot.TryGetValue("HY_OAS", out var highYieldSpread))
        {
            return Missing(definition, "HY_OAS");
        }

        var score = usesResearchV1
            ? 1m - Clamp01((highYieldSpread - 1m) / 3m)
            : 1m - Clamp01((highYieldSpread - 2.5m) / 5m);
        var interpretation = usesResearchV1
            ? "Credit conditions v1 normalized inversely for the long-history BAA10Y proxy over a 1%-4% range."
            : "Credit stress normalized inversely from high-yield spread.";
        return new FeatureNormalizationResultItem(highYieldSpread, score, interpretation, null);
    }

    private static FeatureNormalizationResultItem NormalizeDirectFeature(DataSnapshot snapshot, FeatureDefinition definition)
    {
        if (!snapshot.TryGetValue(definition.Code, out var rawValue))
        {
            return Missing(definition, definition.Code);
        }

        var score = Clamp01(rawValue);
        if (definition.Polarity == FeaturePolarity.HigherIsRiskOff)
        {
            score = 1m - score;
        }

        return new FeatureNormalizationResultItem(rawValue, score, "Direct feature normalized from supplied value.", null);
    }

    private static FeatureNormalizationResultItem Missing(FeatureDefinition definition, string expectedInput)
    {
        return new FeatureNormalizationResultItem(
            0.5m,
            NormalizedScore.Neutral.Value,
            $"Missing input for {definition.Code}; neutral score used.",
            $"Feature {definition.Code} is missing {expectedInput}; neutral score used.");
    }

    private static string? MissingPartial(FeatureDefinition definition, bool hasFirst, bool hasSecond, string first, string second)
    {
        if (hasFirst && hasSecond)
        {
            return null;
        }

        var missing = hasFirst ? second : first;
        return $"Feature {definition.Code} is missing {missing}; neutral component used.";
    }

    private static decimal Clamp01(decimal value)
    {
        return Math.Min(1m, Math.Max(0m, value));
    }

    private static bool UsesResearchV1(FeatureSetVersion featureSetVersion)
    {
        return featureSetVersion.Version.StartsWith("1.", StringComparison.OrdinalIgnoreCase);
    }

    private static bool UsesResearchV11(FeatureSetVersion featureSetVersion)
    {
        return featureSetVersion.Version.StartsWith("1.1", StringComparison.OrdinalIgnoreCase)
            || featureSetVersion.Version.StartsWith("1.2", StringComparison.OrdinalIgnoreCase);
    }

    private static bool UsesResearchV13(FeatureSetVersion featureSetVersion)
    {
        return featureSetVersion.Version.StartsWith("1.3", StringComparison.OrdinalIgnoreCase)
            || featureSetVersion.Version.StartsWith("1.4", StringComparison.OrdinalIgnoreCase);
    }

    private sealed record FeatureNormalizationResultItem(decimal RawValue, decimal Score, string Interpretation, string? Warning);
}
