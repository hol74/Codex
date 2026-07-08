using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Regimes;

public sealed record CalculateRegimeResult
{
    private CalculateRegimeResult(
        bool isSuccess,
        RegimeSnapshot? snapshot,
        DataSnapshotSourceInfo dataSourceInfo,
        string? runLocation,
        string? error)
    {
        IsSuccess = isSuccess;
        Snapshot = snapshot;
        DataSourceInfo = dataSourceInfo;
        RunLocation = runLocation;
        Error = error;
    }

    public bool IsSuccess { get; }

    public RegimeSnapshot? Snapshot { get; }

    public DataSnapshotSourceInfo DataSourceInfo { get; }

    public string? RunLocation { get; }

    public string? Error { get; }

    public static CalculateRegimeResult Success(
        RegimeSnapshot snapshot,
        DataSnapshotSourceInfo? dataSourceInfo = null,
        string? runLocation = null)
    {
        ArgumentNullException.ThrowIfNull(snapshot);

        return new CalculateRegimeResult(true, snapshot, dataSourceInfo ?? DataSnapshotSourceInfo.Unspecified(), runLocation, null);
    }

    public static CalculateRegimeResult Failure(string error)
    {
        if (string.IsNullOrWhiteSpace(error))
        {
            throw new ArgumentException("Failure error is required.", nameof(error));
        }

        return new CalculateRegimeResult(false, null, DataSnapshotSourceInfo.Unspecified(), null, error.Trim());
    }
}
