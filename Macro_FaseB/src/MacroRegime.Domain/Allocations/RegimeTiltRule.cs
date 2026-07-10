using MacroRegime.Domain.Regimes;

namespace MacroRegime.Domain.Allocations;

public sealed record RegimeTiltRule
{
    public RegimeTiltRule(RegimeType regime, AssetClass assetClass, decimal tilt, string reason)
    {
        if (tilt is < -1m or > 1m)
        {
            throw new ArgumentOutOfRangeException(nameof(tilt), "Tilt must be between -1 and 1.");
        }

        if (string.IsNullOrWhiteSpace(reason))
        {
            throw new ArgumentException("Tilt reason is required.", nameof(reason));
        }

        Regime = regime;
        AssetClass = assetClass;
        Tilt = tilt;
        Reason = reason.Trim();
    }

    public RegimeType Regime { get; }

    public AssetClass AssetClass { get; }

    public decimal Tilt { get; }

    public string Reason { get; }
}
