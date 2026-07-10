using MacroRegime.Application.External;
using MacroRegime.Application.Ports;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Tests.External;

public sealed class DownloadMacroDataUseCaseTests
{
    [Fact]
    public async Task ExecuteAsync_WritesFile_WithCorrectNameAndSeriesCount()
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var observations = new[]
        {
            new FredObservation("INDPRO", "INDPRO_YOY", asOf.Value, asOf.Value, asOf.Value, 2.0m, "Percent change"),
            new FredObservation("VIXCLS", "VIX", asOf.Value, asOf.Value, asOf.Value, 18.0m, "Index"),
        };
        var source = new FakeExternalMacroDataSource(observations);
        var writer = new FakeMacroDataFileWriter();
        var useCase = new DownloadMacroDataUseCase(source, writer);

        var result = await useCase.ExecuteAsync(
            new DownloadMacroDataCommand(asOf, FredSeriesSet.Baseline, "/tmp/out"));

        Assert.Equal(2, result.SeriesCount);
        Assert.Equal(2, result.ObservationCount);
        Assert.Equal(Path.Combine("/tmp/out", "macro-data-2026-07-01.json"), result.OutputPath);
        Assert.Equal(asOf, writer.LastAsOf);
        Assert.Equal(2, writer.LastObservations!.Count);
    }

    [Fact]
    public async Task ExecuteAsync_RequestsBaselineSeries_FromSource()
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var source = new FakeExternalMacroDataSource(Array.Empty<FredObservation>());
        var writer = new FakeMacroDataFileWriter();
        var useCase = new DownloadMacroDataUseCase(source, writer);

        await useCase.ExecuteAsync(new DownloadMacroDataCommand(asOf, FredSeriesSet.Baseline, "/tmp/out"));

        Assert.Equal(FredSeriesSet.Baseline, source.LastCommand?.SeriesSet);
        Assert.Equal(asOf, source.LastCommand?.AsOfDate);
    }

    [Fact]
    public async Task ExecuteAsync_Throws_WhenSeriesSetIsEmpty()
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var useCase = new DownloadMacroDataUseCase(
            new FakeExternalMacroDataSource(Array.Empty<FredObservation>()),
            new FakeMacroDataFileWriter());

        await Assert.ThrowsAsync<ArgumentException>(() =>
            useCase.ExecuteAsync(new DownloadMacroDataCommand(asOf, new FredSeriesSet(Array.Empty<string>()), "/tmp/out")));
    }

    private sealed class FakeExternalMacroDataSource : IExternalMacroDataSource
    {
        private readonly IReadOnlyList<FredObservation> observations;
        public FredFetchCommand? LastCommand { get; private set; }

        public FakeExternalMacroDataSource(IReadOnlyList<FredObservation> observations)
        {
            this.observations = observations;
        }

        public Task<IReadOnlyList<FredObservation>> FetchAsync(FredFetchCommand command, CancellationToken cancellationToken = default)
        {
            LastCommand = command;
            return Task.FromResult(observations);
        }
    }

    private sealed class FakeMacroDataFileWriter : IMacroDataFileWriter
    {
        public IReadOnlyList<FredObservation>? LastObservations { get; private set; }
        public AsOfDate? LastAsOf { get; private set; }

        public Task<string> WriteAsync(IReadOnlyList<FredObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken cancellationToken = default)
        {
            LastObservations = observations;
            LastAsOf = asOfDate;
            return Task.FromResult(Path.Combine(outputDirectory, $"macro-data-{asOfDate.Value:yyyy-MM-dd}.json"));
        }
    }
}
