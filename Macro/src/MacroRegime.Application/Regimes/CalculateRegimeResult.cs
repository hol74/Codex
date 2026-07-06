using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Regimes;

public sealed record CalculateRegimeResult
{
    private CalculateRegimeResult(
        bool isSuccess,
        RegimeSnapshot? snapshot,
        DataSnapshotSourceInfo dataSourceInfo,
        string? error)
    {
        IsSuccess = isSuccess;
        Snapshot = snapshot;
        DataSourceInfo = dataSourceInfo;
        Error = error;
    }

    public bool IsSuccess { get; }

    public RegimeSnapshot? Snapshot { get; }

    public DataSnapshotSourceInfo DataSourceInfo { get; }

    public string? Error { get; }

    public static CalculateRegimeResult Success(RegimeSnapshot snapshot, DataSnapshotSourceInfo? dataSourceInfo = null)
    {
        ArgumentNullException.ThrowIfNull(snapshot);

        return new CalculateRegimeResult(true, snapshot, dataSourceInfo ?? DataSnapshotSourceInfo.Unspecified(), null);
    }

    public static CalculateRegimeResult Failure(string error)
    {
        if (string.IsNullOrWhiteSpace(error))
        {
            throw new ArgumentException("Failure error is required.", nameof(error));
        }

        return new CalculateRegimeResult(false, null, DataSnapshotSourceInfo.Unspecified(), error.Trim());
    }
}
