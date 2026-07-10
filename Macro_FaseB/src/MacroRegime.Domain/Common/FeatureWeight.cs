namespace MacroRegime.Domain.Common;

public readonly record struct FeatureWeight
{
    public FeatureWeight(decimal value)
    {
        if (value < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "Feature weight cannot be negative.");
        }

        Value = value;
    }

    public decimal Value { get; }

    public override string ToString()
    {
        return Value.ToString("0.####");
    }
}
