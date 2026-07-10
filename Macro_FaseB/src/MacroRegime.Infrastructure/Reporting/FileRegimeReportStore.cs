using MacroRegime.Application.Ports;

namespace MacroRegime.Infrastructure.Reporting;

public sealed class FileRegimeReportStore : IRegimeReportStore
{
    private readonly string directoryPath;

    public FileRegimeReportStore(string directoryPath)
    {
        if (string.IsNullOrWhiteSpace(directoryPath))
        {
            throw new ArgumentException("Directory path is required.", nameof(directoryPath));
        }

        this.directoryPath = directoryPath;
    }

    public async Task<string> SaveMarkdownAsync(DateOnly asOfDate, string markdown, CancellationToken cancellationToken = default)
    {
        if (asOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "As-of date is required.");
        }

        if (markdown is null)
        {
            throw new ArgumentNullException(nameof(markdown));
        }

        Directory.CreateDirectory(directoryPath);

        var path = GetPath(asOfDate);
        await File.WriteAllTextAsync(path, markdown, cancellationToken).ConfigureAwait(false);

        return path;
    }

    public string GetPath(DateOnly asOfDate)
    {
        if (asOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "As-of date is required.");
        }

        return Path.Combine(directoryPath, $"macro-regime-report-{asOfDate:yyyy-MM-dd}.md");
    }
}
