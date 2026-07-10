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
            var result = NormalizeFeature(snapshot, definition);
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

    private static FeatureNormalizationResultItem NormalizeFeature(DataSnapshot snapshot, FeatureDefinition definition)
    {
        return definition.Code.ToUpperInvariant() switch
        {
            "GROWTH_MOM" => NormalizeGrowthMomentum(snapshot, definition),
            "INFL_PRESS" => NormalizeInflationPressure(snapshot, definition),
            "RISK_APPETITE" => NormalizeRiskAppetite(snapshot, definition),
            "MONETARY_COND" => NormalizeMonetaryConditions(snapshot, definition),
            "CREDIT_STRESS" => NormalizeCreditStress(snapshot, definition),
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

    private static FeatureNormalizationResultItem NormalizeInflationPressure(DataSnapshot snapshot, FeatureDefinition definition)
    {
        if (!snapshot.TryGetValue("T10YIE", out var breakeven))
        {
            return Missing(definition, "T10YIE");
        }

        var score = Clamp01((breakeven - 1m) / 2.5m);
        return new FeatureNormalizationResultItem(breakeven, score, "Inflation pressure normalized from breakeven inflation.", null);
    }

    private static FeatureNormalizationResultItem NormalizeRiskAppetite(DataSnapshot snapshot, FeatureDefinition definition)
    {
        if (!snapshot.TryGetValue("VIX", out var vix))
        {
            return Missing(definition, "VIX");
        }

        var score = 1m - Clamp01((vix - 12m) / 28m);
        return new FeatureNormalizationResultItem(vix, score, "Risk appetite normalized inversely from VIX.", null);
    }

    private static FeatureNormalizationResultItem NormalizeMonetaryConditions(DataSnapshot snapshot, FeatureDefinition definition)
    {
        if (!snapshot.TryGetValue("YC_10Y2Y", out var curve))
        {
            return Missing(definition, "YC_10Y2Y");
        }

        var score = Clamp01((curve + 1m) / 2m);
        return new FeatureNormalizationResultItem(curve, score, "Monetary conditions normalized from 10Y-2Y curve slope.", null);
    }

    private static FeatureNormalizationResultItem NormalizeCreditStress(DataSnapshot snapshot, FeatureDefinition definition)
    {
        if (!snapshot.TryGetValue("HY_OAS", out var highYieldSpread))
        {
            return Missing(definition, "HY_OAS");
        }

        var score = 1m - Clamp01((highYieldSpread - 2.5m) / 5m);
        return new FeatureNormalizationResultItem(highYieldSpread, score, "Credit stress normalized inversely from high-yield spread.", null);
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

    private sealed record FeatureNormalizationResultItem(decimal RawValue, decimal Score, string Interpretation, string? Warning);
}
