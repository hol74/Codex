using MacroRegime.Application.Regimes;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Analysis;

public sealed record RunRegimeAnalysisResult
{
    private RunRegimeAnalysisResult(
        bool isSuccess,
        RegimeSnapshot? snapshot,
        AllocationProposal? allocationProposal,
        DataSnapshotSourceInfo dataSourceInfo,
        string? markdown,
        string? reportLocation,
        string? runLocation,
        string? error)
    {
        IsSuccess = isSuccess;
        Snapshot = snapshot;
        AllocationProposal = allocationProposal;
        DataSourceInfo = dataSourceInfo;
        Markdown = markdown;
        ReportLocation = reportLocation;
        RunLocation = runLocation;
        Error = error;
    }

    public bool IsSuccess { get; }

    public RegimeSnapshot? Snapshot { get; }

    public AllocationProposal? AllocationProposal { get; }

    public DataSnapshotSourceInfo DataSourceInfo { get; }

    public string? Markdown { get; }

    public string? ReportLocation { get; }

    public string? RunLocation { get; }

    public string? Error { get; }

    public static RunRegimeAnalysisResult Success(
        RegimeSnapshot snapshot,
        AllocationProposal allocationProposal,
        string markdown,
        string reportLocation,
        string? runLocation = null,
        DataSnapshotSourceInfo? dataSourceInfo = null)
    {
        ArgumentNullException.ThrowIfNull(snapshot);
        ArgumentNullException.ThrowIfNull(allocationProposal);

        if (string.IsNullOrWhiteSpace(markdown))
        {
            throw new ArgumentException("Markdown report is required.", nameof(markdown));
        }

        if (string.IsNullOrWhiteSpace(reportLocation))
        {
            throw new ArgumentException("Report location is required.", nameof(reportLocation));
        }

        return new RunRegimeAnalysisResult(
            true,
            snapshot,
            allocationProposal,
            dataSourceInfo ?? DataSnapshotSourceInfo.Unspecified(),
            markdown,
            reportLocation.Trim(),
            string.IsNullOrWhiteSpace(runLocation) ? null : runLocation.Trim(),
            null);
    }

    public static RunRegimeAnalysisResult Failure(string error)
    {
        if (string.IsNullOrWhiteSpace(error))
        {
            throw new ArgumentException("Failure error is required.", nameof(error));
        }

        return new RunRegimeAnalysisResult(false, null, null, DataSnapshotSourceInfo.Unspecified(), null, null, null, error.Trim());
    }
}
