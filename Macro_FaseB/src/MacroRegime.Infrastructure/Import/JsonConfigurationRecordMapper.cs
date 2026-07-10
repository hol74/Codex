using System.Globalization;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Infrastructure.Import;

public static class JsonConfigurationRecordMapper
{
    public const int CurrentSchemaVersion = 1;

    public static ModelVersion ToModelVersion(JsonModelVersionRecord record)
    {
        ArgumentNullException.ThrowIfNull(record);
        EnsureSchemaVersion(record.SchemaVersion, "model version");

        if (record.EffectiveFrom == DateOnly.MinValue)
        {
            throw new InvalidDataException("Model effective date is required.");
        }

        return new ModelVersion(
            Require(record.Name, "Model name is required."),
            Require(record.Version, "Model version is required."),
            ParseEnum<ModelRole>(record.Role, "Model role"),
            record.Parameters ?? new Dictionary<string, decimal>(StringComparer.OrdinalIgnoreCase),
            record.EffectiveFrom,
            record.Description ?? string.Empty);
    }

    public static FeatureSetVersion ToFeatureSetVersion(JsonFeatureSetVersionRecord record)
    {
        ArgumentNullException.ThrowIfNull(record);
        EnsureSchemaVersion(record.SchemaVersion, "feature set");

        if (record.FeatureDefinitions is null)
        {
            throw new InvalidDataException("Feature definitions array is required.");
        }

        return new FeatureSetVersion(
            Require(record.Name, "Feature set name is required."),
            Require(record.Version, "Feature set version is required."),
            record.FeatureDefinitions.Select(ToFeatureDefinition).ToArray());
    }

    public static StrategicAllocationPolicy ToStrategicAllocationPolicy(JsonStrategicAllocationPolicyRecord record)
    {
        ArgumentNullException.ThrowIfNull(record);
        EnsureSchemaVersion(record.SchemaVersion, "allocation policy");

        if (record.Bands is null)
        {
            throw new InvalidDataException("Allocation bands array is required.");
        }

        return new StrategicAllocationPolicy(
            Require(record.Name, "Allocation policy name is required."),
            record.Bands.Select(ToAllocationBand).ToArray(),
            new AllocationWeight(record.MaximumTurnover),
            record.MaximumEstimatedCost);
    }

    public static CurrentPortfolio ToCurrentPortfolio(JsonCurrentPortfolioRecord record)
    {
        ArgumentNullException.ThrowIfNull(record);
        EnsureSchemaVersion(record.SchemaVersion, "current portfolio");

        if (record.AsOfDate == DateOnly.MinValue)
        {
            throw new InvalidDataException("Current portfolio as-of date is required.");
        }

        if (record.Weights is null)
        {
            throw new InvalidDataException("Portfolio weights array is required.");
        }

        return new CurrentPortfolio(record.Weights.Select(ToPortfolioWeight).ToArray());
    }

    public static IReadOnlyList<RegimeTiltRule> ToTiltRules(JsonRegimeTiltRulesRecord record)
    {
        ArgumentNullException.ThrowIfNull(record);
        EnsureSchemaVersion(record.SchemaVersion, "regime tilt rules");

        if (record.Rules is null)
        {
            throw new InvalidDataException("Regime tilt rules array is required.");
        }

        return record.Rules.Select(ToTiltRule).ToArray();
    }

    private static FeatureDefinition ToFeatureDefinition(JsonFeatureDefinitionRecord record)
    {
        return new FeatureDefinition(
            Require(record.Code, "Feature code is required."),
            Require(record.Name, "Feature name is required."),
            ParseEnum<EconomicDimension>(record.Dimension, "Economic dimension"),
            record.FormulaDescription ?? string.Empty,
            new FeatureWeight(record.Weight),
            ParseEnum<FeaturePolarity>(record.Polarity, "Feature polarity"),
            record.LookbackMonths,
            record.IsActive);
    }

    private static AllocationBand ToAllocationBand(JsonAllocationBandRecord record)
    {
        return new AllocationBand(
            ParseEnum<AssetClass>(record.AssetClass, "Asset class"),
            new AllocationWeight(record.Minimum),
            new AllocationWeight(record.Strategic),
            new AllocationWeight(record.Maximum));
    }

    private static PortfolioWeight ToPortfolioWeight(JsonPortfolioWeightRecord record)
    {
        return new PortfolioWeight(
            ParseEnum<AssetClass>(record.AssetClass, "Asset class"),
            new AllocationWeight(record.Weight));
    }

    private static RegimeTiltRule ToTiltRule(JsonRegimeTiltRuleRecord record)
    {
        return new RegimeTiltRule(
            ParseEnum<RegimeType>(record.Regime, "Regime"),
            ParseEnum<AssetClass>(record.AssetClass, "Asset class"),
            record.Tilt,
            Require(record.Reason, "Tilt reason is required."));
    }

    private static void EnsureSchemaVersion(int schemaVersion, string description)
    {
        if (schemaVersion != CurrentSchemaVersion)
        {
            throw new InvalidDataException($"Unsupported {description} schema version {schemaVersion}. Expected {CurrentSchemaVersion}.");
        }
    }

    private static TEnum ParseEnum<TEnum>(string? value, string description)
        where TEnum : struct
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidDataException($"{description} is required.");
        }

        if (!Enum.TryParse<TEnum>(value.Trim(), ignoreCase: true, out var parsed))
        {
            throw new InvalidDataException(string.Format(CultureInfo.InvariantCulture, "{0} '{1}' is not supported.", description, value));
        }

        return parsed;
    }

    private static string Require(string? value, string message)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidDataException(message);
        }

        return value.Trim();
    }
}
