using MacroRegime.Application.Ports;
using MacroRegime.Application.Runs;

namespace MacroRegime.Application.Tests.Runs;

public sealed class LoadRegimeRunUseCaseTests
{
    [Fact]
    public async Task ExecuteAsync_ReturnsStoredDocument_WithoutRecalculation()
    {
        var document = RegimeRunTestFixtures.CreateDocument(new DateOnly(2026, 7, 1));
        var store = new InMemoryRegimeRunStore(document);
        var useCase = new LoadRegimeRunUseCase(store);

        var result = await useCase.ExecuteAsync(new LoadRegimeRunCommand(new DateOnly(2026, 7, 1)));

        Assert.True(result.IsSuccess);
        Assert.Same(document, result.Document);
        Assert.Equal(0, store.SaveCount);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsFailure_WhenRunIsMissing()
    {
        var useCase = new LoadRegimeRunUseCase(new InMemoryRegimeRunStore());

        var result = await useCase.ExecuteAsync(new LoadRegimeRunCommand(new DateOnly(2026, 7, 1)));

        Assert.False(result.IsSuccess);
        Assert.Null(result.Document);
        Assert.Contains("2026-07-01", result.Error);
    }

    [Fact]
    public void Command_RejectsMissingAsOfDate()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new LoadRegimeRunCommand(DateOnly.MinValue));
    }
}

internal sealed class InMemoryRegimeRunStore : IRegimeRunStore
{
    private readonly Dictionary<DateOnly, RegimeRunDocument> documents = new();

    public InMemoryRegimeRunStore(params RegimeRunDocument[] initialDocuments)
    {
        foreach (var document in initialDocuments)
        {
            documents[document.AsOfDate] = document;
        }
    }

    public int SaveCount { get; private set; }

    public Task<string> SaveAsync(RegimeRunDocument document, CancellationToken cancellationToken = default)
    {
        SaveCount++;
        documents[document.AsOfDate] = document;
        return Task.FromResult($"memory://regime-run-{document.AsOfDate:yyyy-MM-dd}.json");
    }

    public Task<RegimeRunDocument?> LoadAsync(DateOnly asOfDate, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(documents.TryGetValue(asOfDate, out var document) ? document : null);
    }
}

internal static class RegimeRunTestFixtures
{
    public static RegimeRunDocument CreateDocument(
        DateOnly asOfDate,
        string primaryRegime = "Goldilocks",
        decimal primaryProbability = 0.7m,
        decimal confidence = 0.7m,
        decimal growthScore = 0.8m,
        string allocationSuggestion = "PartialRebalance",
        decimal equityTarget = 0.65m)
    {
        var secondaryRegime = primaryRegime == "Reflation" ? "Goldilocks" : "Reflation";

        return new RegimeRunDocument(
            asOfDate,
            "CRS Rule-Based Engine",
            "0.1",
            "CRS Baseline",
            "0.1",
            primaryRegime,
            primaryRegime,
            confidence,
            0.65m,
            "Confirmed",
            new[]
            {
                new RegimeRunProbability(primaryRegime, primaryProbability, 1),
                new RegimeRunProbability(secondaryRegime, 1m - primaryProbability, 2)
            },
            new[]
            {
                new RegimeRunFeatureScore(
                    "GROWTH_MOM",
                    "Growth momentum",
                    "Growth",
                    1m,
                    55m,
                    growthScore,
                    null,
                    null,
                    "Growth is constructive.")
            },
            new[]
            {
                new RegimeRunExplanation(
                    "Growth momentum is a driver",
                    "Fixture explanation",
                    0.3m,
                    "GROWTH_MOM",
                    "Driver")
            },
            Array.Empty<string>(),
            new RegimeRunDataSource("Imported", "Data snapshot imported from local JSON file.", "memory://data.json"),
            new RegimeRunAllocation(
                allocationSuggestion,
                0.05m,
                0.00005m,
                new[]
                {
                    new RegimeRunAllocationLine("Cash", 0.05m, 0.05m, 1m - equityTarget - 0.3m, 0.02m, 0.20m, 0m, 0m),
                    new RegimeRunAllocationLine("GlobalEquity", 0.60m, 0.60m, equityTarget, 0.45m, 0.75m, 0.05m, equityTarget - 0.60m),
                    new RegimeRunAllocationLine("GovernmentBonds", 0.25m, 0.25m, 0.20m, 0.10m, 0.40m, -0.05m, -0.05m),
                    new RegimeRunAllocationLine("Gold", 0.10m, 0.10m, 0.10m, 0.00m, 0.20m, 0m, 0m)
                },
                new[] { "Constructive growth supports equity tilt." },
                Array.Empty<string>()));
    }
}
