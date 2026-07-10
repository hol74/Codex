using MacroRegime.Domain.Common;

namespace MacroRegime.Domain.Features;

public sealed record FeatureDefinition
{
    public FeatureDefinition(
        string code,
        string name,
        EconomicDimension dimension,
        string formulaDescription,
        FeatureWeight weight,
        FeaturePolarity polarity,
        int lookbackMonths,
        bool isActive)
    {
        if (string.IsNullOrWhiteSpace(code))
        {
            throw new ArgumentException("Feature code is required.", nameof(code));
        }

        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Feature name is required.", nameof(name));
        }

        if (lookbackMonths < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(lookbackMonths), "Lookback months cannot be negative.");
        }

        Code = code.Trim();
        Name = name.Trim();
        Dimension = dimension;
        FormulaDescription = formulaDescription?.Trim() ?? string.Empty;
        Weight = weight;
        Polarity = polarity;
        LookbackMonths = lookbackMonths;
        IsActive = isActive;
    }

    public string Code { get; }

    public string Name { get; }

    public EconomicDimension Dimension { get; }

    public string FormulaDescription { get; }

    public FeatureWeight Weight { get; }

    public FeaturePolarity Polarity { get; }

    public int LookbackMonths { get; }

    public bool IsActive { get; }
}
