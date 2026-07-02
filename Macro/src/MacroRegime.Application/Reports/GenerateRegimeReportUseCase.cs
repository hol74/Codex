using MacroRegime.Application.Ports;

namespace MacroRegime.Application.Reports;

public sealed class GenerateRegimeReportUseCase
{
    private readonly IRegimeReportRenderer renderer;
    private readonly IRegimeReportStore store;

    public GenerateRegimeReportUseCase(IRegimeReportRenderer renderer, IRegimeReportStore store)
    {
        this.renderer = renderer ?? throw new ArgumentNullException(nameof(renderer));
        this.store = store ?? throw new ArgumentNullException(nameof(store));
    }

    public async Task<GenerateRegimeReportResult> ExecuteAsync(
        GenerateRegimeReportCommand command,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);

        var markdown = renderer.Render(command.Content);
        var location = await store.SaveMarkdownAsync(command.Snapshot.AsOfDate.Value, markdown, cancellationToken).ConfigureAwait(false);

        return new GenerateRegimeReportResult(markdown, location);
    }
}
