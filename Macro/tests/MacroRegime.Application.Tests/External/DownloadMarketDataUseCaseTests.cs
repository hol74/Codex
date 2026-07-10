using MacroRegime.Application.External;
using MacroRegime.Application.Ports;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Tests.External;

public sealed class DownloadMarketDataUseCaseTests
{
    [Fact]
    public async Task ExecuteAsync_WritesFile_WithCorrectNameAndSeriesCount()
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var observations = new[]
        {
            new MarketDataObservation("SPY", "SPY", asOf.Value, asOf.Value, 512.34m, "Adjusted close"),
            new MarketDataObservation("GLD", "GLD", asOf.Value, asOf.Value, 221.10m, "Adjusted close"),
        };
        var source = new FakeExternalMarketDataSource(observations);
        var writer = new FakeMarketDataFileWriter();
        var useCase = new DownloadMarketDataUseCase(source, writer);

        var result = await useCase.ExecuteAsync(
            new DownloadMarketDataCommand(asOf, MarketDataSeriesSet.Baseline, "/tmp/out"));

        Assert.Equal(6, result.SeriesCount);
        Assert.Equal(2, result.ObservationCount);
        Assert.Equal(Path.Combine("/tmp/out", "market-data-2026-07-01.json"), result.OutputPath);
        Assert.Equal(asOf, writer.LastAsOf);
        Assert.Equal(2, writer.LastObservations!.Count);
    }

    [Fact]
    public async Task ExecuteAsync_RequestsBaselineSeries_FromSource()
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var source = new FakeExternalMarketDataSource(Array.Empty<MarketDataObservation>());
        var writer = new FakeMarketDataFileWriter();
        var useCase = new DownloadMarketDataUseCase(source, writer);

        await useCase.ExecuteAsync(new DownloadMarketDataCommand(asOf, MarketDataSeriesSet.Baseline, "/tmp/out"));

        Assert.Equal(MarketDataSeriesSet.Baseline, source.LastCommand?.SeriesSet);
        Assert.Equal(asOf, source.LastCommand?.AsOfDate);
    }

    [Fact]
    public async Task ExecuteAsync_Throws_WhenSeriesSetIsEmpty()
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var useCase = new DownloadMarketDataUseCase(
            new FakeExternalMarketDataSource(Array.Empty<MarketDataObservation>()),
            new FakeMarketDataFileWriter());

        await Assert.ThrowsAsync<ArgumentException>(() =>
            useCase.ExecuteAsync(new DownloadMarketDataCommand(asOf, new MarketDataSeriesSet(Array.Empty<string>()), "/tmp/out")));
    }

    private sealed class FakeExternalMarketDataSource : IExternalMarketDataSource
    {
        private readonly IReadOnlyList<MarketDataObservation> observations;
        public MarketDataFetchCommand? LastCommand { get; private set; }

        public FakeExternalMarketDataSource(IReadOnlyList<MarketDataObservation> observations)
        {
            this.observations = observations;
        }

        public Task<IReadOnlyList<MarketDataObservation>> FetchAsync(MarketDataFetchCommand command, CancellationToken cancellationToken = default)
        {
            LastCommand = command;
            return Task.FromResult(observations);
        }
    }

    private sealed class FakeMarketDataFileWriter : IMarketDataFileWriter
    {
        public IReadOnlyList<MarketDataObservation>? LastObservations { get; private set; }
        public AsOfDate? LastAsOf { get; private set; }

        public Task<string> WriteAsync(IReadOnlyList<MarketDataObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken cancellationToken = default)
        {
            LastObservations = observations;
            LastAsOf = asOfDate;
            return Task.FromResult(Path.Combine(outputDirectory, $"market-data-{asOfDate.Value:yyyy-MM-dd}.json"));
        }
    }
}
