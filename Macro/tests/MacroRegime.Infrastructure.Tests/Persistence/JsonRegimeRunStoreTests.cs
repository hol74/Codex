using System.Text.Json;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Explanations;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.Persistence;

namespace MacroRegime.Infrastructure.Tests.Persistence;

public sealed class JsonRegimeRunStoreTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task SaveAsync_WritesMappedRegimeRunRecordAsJson()
    {
        var snapshot = CreateSnapshot();
        var store = new JsonRegimeRunStore(directoryPath);

        await store.SaveAsync(snapshot);

        var path = store.GetPath(snapshot.AsOfDate.Value);
        Assert.True(File.Exists(path));

        var json = await File.ReadAllTextAsync(path);
        var record = JsonSerializer.Deserialize<RegimeRunRecord>(json, new JsonSerializerOptions(JsonSerializerDefaults.Web));

        Assert.NotNull(record);
        Assert.Equal(snapshot.AsOfDate.Value, record.AsOfDate);
        Assert.Equal("Goldilocks", record.PrimaryRegime);
        Assert.Equal("Goldilocks", record.OperationalRegime);
        Assert.Equal(2, record.Probabilities.Count);
        Assert.Equal("GROWTH_MOM", Assert.Single(record.FeatureScores).FeatureCode);
    }

    [Fact]
    public void FromSnapshot_MapsSnapshotWithoutInfrastructureConcerns()
    {
        var record = RegimeRunRecordMapper.FromSnapshot(CreateSnapshot());

        Assert.Equal("CRS Rule-Based Engine", record.ModelName);
        Assert.Equal("CRS Baseline", record.FeatureSetName);
        Assert.Equal(0.7m, record.Confidence);
        Assert.Contains(record.Explanations, explanation => explanation.Kind == "Driver");
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
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
            Array.Empty<string>());
    }
}
