namespace Finance.Application.MacroRegime;

public interface IRegimeCalculationService
{
    Task<RegimeCalculationPreview> PreviewAsync(DateOnly asOfDate, Guid? modelVersionId = null, CancellationToken cancellationToken = default);

    Task<RegimeCalculationResult> CalculateAsync(DateOnly asOfDate, Guid? modelVersionId = null, CancellationToken cancellationToken = default);
}

public sealed record RegimeCalculationPreview(
    DateOnly AsOfDate,
    string ModelName,
    string ModelVersion,
    int MacroObservationCount,
    int MarketObservationCount,
    IReadOnlyCollection<string> AvailableDimensions,
    IReadOnlyCollection<string> MissingDimensions,
    IReadOnlyCollection<string> Warnings);

public sealed record RegimeCalculationResult(
    DateOnly AsOfDate,
    string ModelName,
    string ModelVersion,
    string PrimaryRegime,
    decimal Confidence,
    decimal CompositeScore,
    string Status,
    IReadOnlyCollection<CalculatedFeatureResult> Features,
    IReadOnlyCollection<CalculatedRegimeProbability> Probabilities,
    IReadOnlyCollection<string> Warnings);

public sealed record CalculatedFeatureResult(
    string Code,
    string Name,
    string Dimension,
    decimal Weight,
    decimal RawValue,
    decimal NormalizedValue,
    decimal Momentum4Weeks,
    string Interpretation);

public sealed record CalculatedRegimeProbability(
    string Regime,
    decimal Probability,
    int Rank);
