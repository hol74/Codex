namespace MacroRegime.Application.Ports;

public interface IRegimeReportStore
{
    Task<string> SaveMarkdownAsync(DateOnly asOfDate, string markdown, CancellationToken cancellationToken = default);
}
