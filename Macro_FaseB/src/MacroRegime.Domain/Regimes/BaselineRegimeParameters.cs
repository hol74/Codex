using MacroRegime.Domain.Models;

namespace MacroRegime.Domain.Regimes;

public sealed record BaselineRegimeParameters(decimal ConfirmationThreshold)
{
    public static readonly BaselineRegimeParameters Default = new(0.55m);

    public static BaselineRegimeParameters From(ModelVersion modelVersion)
    {
        ArgumentNullException.ThrowIfNull(modelVersion);

        return new BaselineRegimeParameters(
            Get(modelVersion, "confirmation_threshold", Default.ConfirmationThreshold));
    }

    private static decimal Get(ModelVersion modelVersion, string key, decimal defaultValue)
    {
        return modelVersion.Parameters.TryGetValue(key, out var value) ? value : defaultValue;
    }
}
