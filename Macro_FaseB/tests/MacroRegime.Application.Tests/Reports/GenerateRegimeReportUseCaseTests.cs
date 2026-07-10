using MacroRegime.Application.Ports;
using MacroRegime.Application.Reports;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Tests.Reports;

public sealed class GenerateRegimeReportUseCaseTests
{
    [Fact]
    public async Task ExecuteAsync_RendersAndSavesMarkdownReport()
    {
        var renderer = new FakeReportRenderer("# report");
        var store = new FakeReportStore("memory://report.md");
        var useCase = new GenerateRegimeReportUseCase(renderer, store);
        var snapshot = CreateSnapshot();

        var result = await useCase.ExecuteAsync(new GenerateRegimeReportCommand(snapshot));

        Assert.Equal("# report", result.Markdown);
        Assert.Equal("memory://report.md", result.Location);
        Assert.Same(snapshot, renderer.RenderedContent?.Snapshot);
        Assert.Equal(snapshot.AsOfDate.Value, store.AsOfDate);
        Assert.Equal("# report", store.Markdown);
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

        return new RegimeSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            modelVersion,
            new FeatureSetVersion("CRS Baseline", "0.1", new[] { featureDefinition }),
            RegimeType.Goldilocks,
            new RegimeConfidence(0.7m),
            new NormalizedScore(0.65m),
            "Confirmed",
            new[]
            {
                new RegimeProbability(RegimeType.Goldilocks, new Probability(0.7m), 1),
                new RegimeProbability(RegimeType.Reflation, new Probability(0.3m), 2)
            },
            Array.Empty<FeatureScore>(),
            Array.Empty<MacroRegime.Domain.Explanations.RegimeExplanation>(),
            Array.Empty<string>());
    }

    private sealed class FakeReportRenderer(string markdown) : IRegimeReportRenderer
    {
        public RegimeReportContent? RenderedContent { get; private set; }

        public string Render(RegimeReportContent content)
        {
            RenderedContent = content;
            return markdown;
        }
    }

    private sealed class FakeReportStore(string location) : IRegimeReportStore
    {
        public DateOnly? AsOfDate { get; private set; }

        public string? Markdown { get; private set; }

        public Task<string> SaveMarkdownAsync(DateOnly asOfDate, string markdown, CancellationToken cancellationToken = default)
        {
            AsOfDate = asOfDate;
            Markdown = markdown;
            return Task.FromResult(location);
        }
    }
}
