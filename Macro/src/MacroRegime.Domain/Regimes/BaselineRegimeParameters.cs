using MacroRegime.Domain.Models;

namespace MacroRegime.Domain.Regimes;

public sealed record BaselineRegimeParameters(
    decimal ConfirmationThreshold,
    decimal ScoringProfile,
    decimal ConfidenceFitWeight,
    decimal ConfidenceMarginWeight)
{
    public static readonly BaselineRegimeParameters Default = new(0.55m, 1m, 0.55m, 1.5m);

    public static BaselineRegimeParameters From(ModelVersion modelVersion)
    {
        ArgumentNullException.ThrowIfNull(modelVersion);

        return new BaselineRegimeParameters(
            Get(modelVersion, "confirmation_threshold", Default.ConfirmationThreshold),
            Get(modelVersion, "scoring_profile", Default.ScoringProfile),
            Get(modelVersion, "confidence_fit_weight", Default.ConfidenceFitWeight),
            Get(modelVersion, "confidence_margin_weight", Default.ConfidenceMarginWeight));
    }

    private static decimal Get(ModelVersion modelVersion, string key, decimal defaultValue)
    {
        return modelVersion.Parameters.TryGetValue(key, out var value) ? value : defaultValue;
    }
}
