namespace MacroRegime.Infrastructure.Import;

public sealed record JsonModelVersionRecord(
    int SchemaVersion,
    string? Name,
    string? Version,
    string? Role,
    IReadOnlyDictionary<string, decimal>? Parameters,
    DateOnly EffectiveFrom,
    string? Description);

public sealed record JsonFeatureSetVersionRecord(
    int SchemaVersion,
    string? Name,
    string? Version,
    IReadOnlyList<JsonFeatureDefinitionRecord>? FeatureDefinitions);

public sealed record JsonFeatureDefinitionRecord(
    string? Code,
    string? Name,
    string? Dimension,
    string? FormulaDescription,
    decimal Weight,
    string? Polarity,
    int LookbackMonths,
    bool IsActive);

public sealed record JsonStrategicAllocationPolicyRecord(
    int SchemaVersion,
    string? Name,
    IReadOnlyList<JsonAllocationBandRecord>? Bands,
    decimal MaximumTurnover,
    decimal MaximumEstimatedCost);

public sealed record JsonAllocationBandRecord(
    string? AssetClass,
    decimal Minimum,
    decimal Strategic,
    decimal Maximum);

public sealed record JsonCurrentPortfolioRecord(
    int SchemaVersion,
    DateOnly AsOfDate,
    IReadOnlyList<JsonPortfolioWeightRecord>? Weights);

public sealed record JsonPortfolioWeightRecord(
    string? AssetClass,
    decimal Weight);

public sealed record JsonRegimeTiltRulesRecord(
    int SchemaVersion,
    IReadOnlyList<JsonRegimeTiltRuleRecord>? Rules);

public sealed record JsonRegimeTiltRuleRecord(
    string? Regime,
    string? AssetClass,
    decimal Tilt,
    string? Reason);
