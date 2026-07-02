using MacroRegime.Domain.Common;
using MacroRegime.Domain.Explanations;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;
using MacroRegime.Reporting.Markdown;

namespace MacroRegime.Reporting.Tests.Markdown;

public sealed class MarkdownRegimeReportRendererTests
{
    [Fact]
    public void Render_ProducesReadableMarkdownReport()
    {
        var renderer = new MarkdownRegimeReportRenderer();

        var markdown = renderer.Render(CreateSnapshot());

        Assert.Contains("# Macro-Regime Report", markdown);
        Assert.Contains("As-of date: 2026-07-01", markdown);
        Assert.Contains("Primary regime: Goldilocks", markdown);
        Assert.Contains("## Probabilities", markdown);
        Assert.Contains("| 1 | Goldilocks | 0.7 |", markdown);
        Assert.Contains("## Feature Scores", markdown);
        Assert.Contains("GROWTH_MOM", markdown);
        Assert.Contains("## Warnings", markdown);
    }

    private static RegimeSnapshot CreateSnapshot()
    {
        var modelVersion = new ModelVersion(
            "CRS Rule-Based Engine",
            "0.1",
            ModelRole.Baseline,
            new Dictionary<string, decimal>(),
            new DateOnly(2026, 7, 1),
            "Baseline model");

        var featureDefinition = new FeatureDefinition(
            "GROWTH_MOM",
            "Growth momentum",
            EconomicDimension.Growth,
            "Fixture",
            new FeatureWeight(1m),
            FeaturePolarity.HigherIsRiskOn,
            6,
            true);

        var featureSetVersion = new FeatureSetVersion("CRS Baseline", "0.1", new[] { featureDefinition });

        return new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            modelVersion,
            featureSetVersion,
            RegimeType.Goldilocks,
            new RegimeConfidence(0.7m),
            new NormalizedScore(0.65m),
            "Confirmed",
            new[]
            {
                new RegimeProbability(RegimeType.Goldilocks, new Probability(0.7m), 1),
                new RegimeProbability(RegimeType.Reflation, new Probability(0.3m), 2)
            },
            new[]
            {
                new FeatureScore(
                    "GROWTH_MOM",
                    "Growth momentum",
                    EconomicDimension.Growth,
                    new FeatureWeight(1m),
                    55m,
                    new NormalizedScore(0.8m),
                    null,
                    null,
                    "Growth is constructive.")
            },
            new[]
            {
                new RegimeExplanation(
                    "Growth momentum is a driver",
                    "Fixture explanation",
                    0.3m,
                    "GROWTH_MOM",
                    RegimeExplanationKind.Driver)
            },
            new[] { "Fixture warning." });
    }
}
