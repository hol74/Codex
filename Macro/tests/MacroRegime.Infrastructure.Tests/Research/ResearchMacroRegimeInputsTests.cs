using MacroRegime.Infrastructure.Research;

namespace MacroRegime.Infrastructure.Tests.Research;

public sealed class ResearchMacroRegimeInputsTests
{
    [Fact]
    public void CandidateV1IsVersionedAndExplicitlyResearchOnly()
    {
        var featureSet = ResearchMacroRegimeInputs.CreateFeatureSetVersion();
        var model = ResearchMacroRegimeInputs.CreateModelVersion();

        Assert.Equal("1.0-candidate", featureSet.Version);
        Assert.Equal("1.0-candidate", model.Version);
        Assert.Equal(new DateOnly(2026, 7, 13), model.EffectiveFrom);
        Assert.Contains("Research-only", model.Description);
        Assert.Contains(featureSet.FeatureDefinitions, feature =>
            feature.Code == "CREDIT_STRESS" && feature.FormulaDescription.Contains("BAA10Y"));
        Assert.Contains(featureSet.FeatureDefinitions, feature =>
            feature.Code == "INFL_PRESS" && feature.FormulaDescription.Contains("data gap"));
    }

    [Fact]
    public void CandidateV11AddsTemporalInflationAndCurveDefinitionsWithoutChangingThreshold()
    {
        var featureSet = ResearchMacroRegimeInputs.CreateFeatureSetVersionV11();
        var model = ResearchMacroRegimeInputs.CreateModelVersionV11();

        Assert.Equal("1.1-candidate", featureSet.Version);
        Assert.Equal("1.1-candidate", model.Version);
        Assert.Equal(0.55m, model.Parameters["confirmation_threshold"]);
        Assert.Contains(featureSet.FeatureDefinitions, feature =>
            feature.Code == "INFL_PRESS" && feature.FormulaDescription.Contains("CPI YoY three-month change"));
        Assert.Contains(featureSet.FeatureDefinitions, feature =>
            feature.Code == "MONETARY_COND" && feature.FormulaDescription.Contains("three-month change"));
    }

    [Fact]
    public void CandidateV13ChangesOnlyRiskDefinitionAndKeepsArchetypeParameters()
    {
        var v12 = ResearchMacroRegimeInputs.CreateFeatureSetVersionV12();
        var v13 = ResearchMacroRegimeInputs.CreateFeatureSetVersionV13();
        var model = ResearchMacroRegimeInputs.CreateModelVersionV13();

        Assert.Equal("1.3-candidate", v13.Version);
        Assert.Equal("1.3-candidate", model.Version);
        Assert.Equal(12m, model.Parameters["scoring_profile"]);
        Assert.Contains(v13.FeatureDefinitions, feature =>
            feature.Code == "RISK_APPETITE" && feature.FormulaDescription.Contains("logistic VIX"));
        Assert.Equal(
            v12.FeatureDefinitions.Where(feature => feature.Code != "RISK_APPETITE").Select(feature => feature.FormulaDescription),
            v13.FeatureDefinitions.Where(feature => feature.Code != "RISK_APPETITE").Select(feature => feature.FormulaDescription));
    }

    [Fact]
    public void CandidateV14KeepsV13FeaturesAndSelectsGeometricProfile()
    {
        var v13 = ResearchMacroRegimeInputs.CreateFeatureSetVersionV13();
        var v14 = ResearchMacroRegimeInputs.CreateFeatureSetVersionV14();
        var model = ResearchMacroRegimeInputs.CreateModelVersionV14();

        Assert.Equal("1.4-candidate", v14.Version);
        Assert.Equal("1.4-candidate", model.Version);
        Assert.Equal(14m, model.Parameters["scoring_profile"]);
        Assert.Equal(0.75m, model.Parameters["confidence_fit_weight"]);
        Assert.Equal(0.25m, model.Parameters["confidence_margin_weight"]);
        Assert.Equal(
            v13.FeatureDefinitions.Select(feature => feature.FormulaDescription),
            v14.FeatureDefinitions.Select(feature => feature.FormulaDescription));
    }
}
