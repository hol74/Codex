using MacroRegime.Application.Ports;

namespace MacroRegime.Application.Runs;

public sealed class CompareRegimeRunsUseCase
{
    private readonly IRegimeRunStore regimeRunStore;

    public CompareRegimeRunsUseCase(IRegimeRunStore regimeRunStore)
    {
        this.regimeRunStore = regimeRunStore ?? throw new ArgumentNullException(nameof(regimeRunStore));
    }

    public async Task<CompareRegimeRunsResult> ExecuteAsync(
        CompareRegimeRunsCommand command,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);

        var baseline = await regimeRunStore.LoadAsync(command.BaselineAsOfDate, cancellationToken).ConfigureAwait(false);
        if (baseline is null)
        {
            return CompareRegimeRunsResult.Failure(
                $"No stored run found for baseline as-of date {command.BaselineAsOfDate:yyyy-MM-dd}.");
        }

        var comparison = await regimeRunStore.LoadAsync(command.ComparisonAsOfDate, cancellationToken).ConfigureAwait(false);
        if (comparison is null)
        {
            return CompareRegimeRunsResult.Failure(
                $"No stored run found for comparison as-of date {command.ComparisonAsOfDate:yyyy-MM-dd}.");
        }

        return CompareRegimeRunsResult.Success(Compare(baseline, comparison));
    }

    private static RegimeRunComparison Compare(RegimeRunDocument baseline, RegimeRunDocument comparison)
    {
        return new RegimeRunComparison(
            baseline,
            comparison,
            !string.Equals(baseline.PrimaryRegime, comparison.PrimaryRegime, StringComparison.Ordinal),
            !string.Equals(baseline.OperationalRegime, comparison.OperationalRegime, StringComparison.Ordinal),
            comparison.Confidence - baseline.Confidence,
            comparison.CompositeScore - baseline.CompositeScore,
            CompareProbabilities(baseline, comparison),
            CompareFeatures(baseline, comparison),
            CompareAllocations(baseline.Allocation, comparison.Allocation));
    }

    private static IReadOnlyList<RegimeProbabilityDelta> CompareProbabilities(
        RegimeRunDocument baseline,
        RegimeRunDocument comparison)
    {
        var baselineByRegime = baseline.Probabilities.ToDictionary(probability => probability.Regime, StringComparer.Ordinal);
        var comparisonByRegime = comparison.Probabilities.ToDictionary(probability => probability.Regime, StringComparer.Ordinal);
        var regimes = baselineByRegime.Keys.Union(comparisonByRegime.Keys, StringComparer.Ordinal);

        return regimes
            .Select(regime =>
            {
                var baselineProbability = baselineByRegime.TryGetValue(regime, out var left) ? left.Probability : (decimal?)null;
                var comparisonProbability = comparisonByRegime.TryGetValue(regime, out var right) ? right.Probability : (decimal?)null;
                return new RegimeProbabilityDelta(
                    regime,
                    baselineProbability,
                    comparisonProbability,
                    (comparisonProbability ?? 0m) - (baselineProbability ?? 0m));
            })
            .OrderByDescending(delta => delta.ComparisonProbability ?? 0m)
            .ThenByDescending(delta => Math.Abs(delta.Delta))
            .ToArray();
    }

    private static IReadOnlyList<FeatureScoreDelta> CompareFeatures(
        RegimeRunDocument baseline,
        RegimeRunDocument comparison)
    {
        var baselineByCode = baseline.FeatureScores.ToDictionary(score => score.FeatureCode, StringComparer.OrdinalIgnoreCase);
        var comparisonByCode = comparison.FeatureScores.ToDictionary(score => score.FeatureCode, StringComparer.OrdinalIgnoreCase);
        var codes = baselineByCode.Keys.Union(comparisonByCode.Keys, StringComparer.OrdinalIgnoreCase);

        return codes
            .Select(code =>
            {
                baselineByCode.TryGetValue(code, out var left);
                comparisonByCode.TryGetValue(code, out var right);
                return new FeatureScoreDelta(
                    code,
                    right?.Name ?? left?.Name ?? code,
                    left?.NormalizedScore,
                    right?.NormalizedScore,
                    (right?.NormalizedScore ?? 0m) - (left?.NormalizedScore ?? 0m),
                    left?.RawValue,
                    right?.RawValue);
            })
            .OrderByDescending(delta => Math.Abs(delta.Delta))
            .ThenBy(delta => delta.FeatureCode, StringComparer.OrdinalIgnoreCase)
            .ToArray();
    }

    private static AllocationComparison? CompareAllocations(
        RegimeRunAllocation? baseline,
        RegimeRunAllocation? comparison)
    {
        if (baseline is null && comparison is null)
        {
            return null;
        }

        var baselineByAsset = (baseline?.Lines ?? Array.Empty<RegimeRunAllocationLine>())
            .ToDictionary(line => line.AssetClass, StringComparer.Ordinal);
        var comparisonByAsset = (comparison?.Lines ?? Array.Empty<RegimeRunAllocationLine>())
            .ToDictionary(line => line.AssetClass, StringComparer.Ordinal);
        var assetClasses = baselineByAsset.Keys.Union(comparisonByAsset.Keys, StringComparer.Ordinal);

        var lineDeltas = assetClasses
            .Select(assetClass =>
            {
                baselineByAsset.TryGetValue(assetClass, out var left);
                comparisonByAsset.TryGetValue(assetClass, out var right);
                return new AllocationLineDelta(
                    assetClass,
                    left?.TargetWeight,
                    right?.TargetWeight,
                    (right?.TargetWeight ?? 0m) - (left?.TargetWeight ?? 0m));
            })
            .OrderBy(delta => delta.AssetClass, StringComparer.Ordinal)
            .ToArray();

        return new AllocationComparison(
            baseline?.Suggestion,
            comparison?.Suggestion,
            !string.Equals(baseline?.Suggestion, comparison?.Suggestion, StringComparison.Ordinal),
            (comparison?.Turnover ?? 0m) - (baseline?.Turnover ?? 0m),
            (comparison?.EstimatedCost ?? 0m) - (baseline?.EstimatedCost ?? 0m),
            lineDeltas);
    }
}

public sealed record CompareRegimeRunsCommand
{
    public CompareRegimeRunsCommand(DateOnly baselineAsOfDate, DateOnly comparisonAsOfDate)
    {
        if (baselineAsOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(baselineAsOfDate), "Baseline as-of date is required.");
        }

        if (comparisonAsOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(comparisonAsOfDate), "Comparison as-of date is required.");
        }

        BaselineAsOfDate = baselineAsOfDate;
        ComparisonAsOfDate = comparisonAsOfDate;
    }

    public DateOnly BaselineAsOfDate { get; }

    public DateOnly ComparisonAsOfDate { get; }
}

public sealed record CompareRegimeRunsResult
{
    private CompareRegimeRunsResult(bool isSuccess, RegimeRunComparison? comparison, string? error)
    {
        IsSuccess = isSuccess;
        Comparison = comparison;
        Error = error;
    }

    public bool IsSuccess { get; }

    public RegimeRunComparison? Comparison { get; }

    public string? Error { get; }

    public static CompareRegimeRunsResult Success(RegimeRunComparison comparison)
    {
        ArgumentNullException.ThrowIfNull(comparison);
        return new CompareRegimeRunsResult(true, comparison, null);
    }

    public static CompareRegimeRunsResult Failure(string error)
    {
        if (string.IsNullOrWhiteSpace(error))
        {
            throw new ArgumentException("Failure error is required.", nameof(error));
        }

        return new CompareRegimeRunsResult(false, null, error.Trim());
    }
}

public sealed record RegimeRunComparison(
    RegimeRunDocument Baseline,
    RegimeRunDocument Comparison,
    bool PrimaryRegimeChanged,
    bool OperationalRegimeChanged,
    decimal ConfidenceDelta,
    decimal CompositeScoreDelta,
    IReadOnlyList<RegimeProbabilityDelta> ProbabilityDeltas,
    IReadOnlyList<FeatureScoreDelta> FeatureDeltas,
    AllocationComparison? Allocation);

public sealed record RegimeProbabilityDelta(
    string Regime,
    decimal? BaselineProbability,
    decimal? ComparisonProbability,
    decimal Delta);

public sealed record FeatureScoreDelta(
    string FeatureCode,
    string Name,
    decimal? BaselineNormalizedScore,
    decimal? ComparisonNormalizedScore,
    decimal Delta,
    decimal? BaselineRawValue,
    decimal? ComparisonRawValue);

public sealed record AllocationComparison(
    string? BaselineSuggestion,
    string? ComparisonSuggestion,
    bool SuggestionChanged,
    decimal TurnoverDelta,
    decimal EstimatedCostDelta,
    IReadOnlyList<AllocationLineDelta> LineDeltas);

public sealed record AllocationLineDelta(
    string AssetClass,
    decimal? BaselineTargetWeight,
    decimal? ComparisonTargetWeight,
    decimal Delta);
