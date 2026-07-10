using MacroRegime.Application.Ports;

namespace MacroRegime.Application.External;

public sealed class DownloadMacroDataUseCase
{
    private readonly IExternalMacroDataSource source;
    private readonly IMacroDataFileWriter writer;

    public DownloadMacroDataUseCase(IExternalMacroDataSource source, IMacroDataFileWriter writer)
    {
        this.source = source;
        this.writer = writer;
    }

    public async Task<DownloadMacroDataResult> ExecuteAsync(DownloadMacroDataCommand command, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        if (command.SeriesSet.SeriesCodes.Count == 0)
        {
            throw new ArgumentException("Series set must contain at least one series.", nameof(command));
        }

        var observations = await source
            .FetchAsync(new FredFetchCommand(command.AsOfDate, command.SeriesSet), cancellationToken)
            .ConfigureAwait(false);
        var outputPath = await writer
            .WriteAsync(observations, command.AsOfDate, command.OutputDirectory, cancellationToken)
            .ConfigureAwait(false);
        var seriesCount = observations.Select(o => o.SeriesCode).Distinct().Count();
        return new DownloadMacroDataResult(outputPath, seriesCount, observations.Count);
    }
}
