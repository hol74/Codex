using MacroRegime.Application.Ports;

namespace MacroRegime.Application.Runs;

public sealed class LoadRegimeRunUseCase
{
    private readonly IRegimeRunStore regimeRunStore;

    public LoadRegimeRunUseCase(IRegimeRunStore regimeRunStore)
    {
        this.regimeRunStore = regimeRunStore ?? throw new ArgumentNullException(nameof(regimeRunStore));
    }

    public async Task<LoadRegimeRunResult> ExecuteAsync(
        LoadRegimeRunCommand command,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);

        var document = await regimeRunStore.LoadAsync(command.AsOfDate, cancellationToken).ConfigureAwait(false);
        if (document is null)
        {
            return LoadRegimeRunResult.Failure(
                $"No stored run found for as-of date {command.AsOfDate:yyyy-MM-dd}.");
        }

        return LoadRegimeRunResult.Success(document);
    }
}

public sealed record LoadRegimeRunCommand
{
    public LoadRegimeRunCommand(DateOnly asOfDate)
    {
        if (asOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "As-of date is required.");
        }

        AsOfDate = asOfDate;
    }

    public DateOnly AsOfDate { get; }
}

public sealed record LoadRegimeRunResult
{
    private LoadRegimeRunResult(bool isSuccess, RegimeRunDocument? document, string? error)
    {
        IsSuccess = isSuccess;
        Document = document;
        Error = error;
    }

    public bool IsSuccess { get; }

    public RegimeRunDocument? Document { get; }

    public string? Error { get; }

    public static LoadRegimeRunResult Success(RegimeRunDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);
        return new LoadRegimeRunResult(true, document, null);
    }

    public static LoadRegimeRunResult Failure(string error)
    {
        if (string.IsNullOrWhiteSpace(error))
        {
            throw new ArgumentException("Failure error is required.", nameof(error));
        }

        return new LoadRegimeRunResult(false, null, error.Trim());
    }
}
