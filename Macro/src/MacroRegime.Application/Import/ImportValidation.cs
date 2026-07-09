namespace MacroRegime.Application.Import;

public sealed record ValidateImportCommand
{
    public ValidateImportCommand(
        DateOnly asOfDate,
        string? dataFilePath,
        string? modelFilePath,
        string? featureSetFilePath,
        string? policyFilePath,
        string? portfolioFilePath,
        string? tiltsFilePath,
        bool strictData,
        bool strictConfig)
    {
        if (asOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "As-of date is required.");
        }

        AsOfDate = asOfDate;
        DataFilePath = dataFilePath;
        ModelFilePath = modelFilePath;
        FeatureSetFilePath = featureSetFilePath;
        PolicyFilePath = policyFilePath;
        PortfolioFilePath = portfolioFilePath;
        TiltsFilePath = tiltsFilePath;
        StrictData = strictData;
        StrictConfig = strictConfig;
    }

    public DateOnly AsOfDate { get; }

    public string? DataFilePath { get; }

    public string? ModelFilePath { get; }

    public string? FeatureSetFilePath { get; }

    public string? PolicyFilePath { get; }

    public string? PortfolioFilePath { get; }

    public string? TiltsFilePath { get; }

    public bool StrictData { get; }

    public bool StrictConfig { get; }
}

public sealed record ImportValidationReport(
    DateOnly AsOfDate,
    IReadOnlyList<ImportValidationItem> Items)
{
    public bool IsSuccess => ErrorCount == 0;

    public int OkCount => Items.Count(item => item.Severity == ImportValidationSeverity.Ok);

    public int WarningCount => Items.Count(item => item.Severity == ImportValidationSeverity.Warning);

    public int ErrorCount => Items.Count(item => item.Severity == ImportValidationSeverity.Error);
}

public sealed record ImportValidationItem(
    string InputKind,
    string? Path,
    ImportValidationSeverity Severity,
    string Message);

public enum ImportValidationSeverity
{
    Ok,
    Warning,
    Error
}
