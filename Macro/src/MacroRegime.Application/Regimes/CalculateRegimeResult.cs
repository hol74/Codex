using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Regimes;

public sealed record CalculateRegimeResult
{
    private CalculateRegimeResult(bool isSuccess, RegimeSnapshot? snapshot, string? error)
    {
        IsSuccess = isSuccess;
        Snapshot = snapshot;
        Error = error;
    }

    public bool IsSuccess { get; }

    public RegimeSnapshot? Snapshot { get; }

    public string? Error { get; }

    public static CalculateRegimeResult Success(RegimeSnapshot snapshot)
    {
        ArgumentNullException.ThrowIfNull(snapshot);

        return new CalculateRegimeResult(true, snapshot, null);
    }

    public static CalculateRegimeResult Failure(string error)
    {
        if (string.IsNullOrWhiteSpace(error))
        {
            throw new ArgumentException("Failure error is required.", nameof(error));
        }

        return new CalculateRegimeResult(false, null, error.Trim());
    }
}
