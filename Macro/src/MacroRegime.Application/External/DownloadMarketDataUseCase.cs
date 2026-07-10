using MacroRegime.Application.Ports;

namespace MacroRegime.Application.External;

public sealed class DownloadMarketDataUseCase
{
    private readonly IExternalMarketDataSource source;
    private readonly IMarketDataFileWriter writer;

    public DownloadMarketDataUseCase(IExternalMarketDataSource source, IMarketDataFileWriter writer)
    {
        this.source = source ?? throw new ArgumentNullException(nameof(source));
        this.writer = writer ?? throw new ArgumentNullException(nameof(writer));
    }

    public async Task<DownloadMarketDataResult> ExecuteAsync(DownloadMarketDataCommand command, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        if (command.SeriesSet.Symbols.Count == 0)
        {
            throw new ArgumentException("At least one market data symbol is required.", nameof(command));
        }

        var observations = await source
            .FetchAsync(new MarketDataFetchCommand(command.AsOfDate, command.SeriesSet), cancellationToken)
            .ConfigureAwait(false);
        var outputPath = await writer
            .WriteAsync(observations, command.AsOfDate, command.OutputDirectory, cancellationToken)
            .ConfigureAwait(false);

        return new DownloadMarketDataResult(outputPath, command.SeriesSet.Symbols.Count, observations.Count);
    }
}
