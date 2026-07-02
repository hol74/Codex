namespace MacroRegime.Domain.Common;

public readonly record struct RegimeConfidence
{
    public RegimeConfidence(decimal value)
    {
        if (value is < 0m or > 1m)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "Regime confidence must be between 0 and 1.");
        }

        Value = value;
    }

    public decimal Value { get; }

    public override string ToString()
    {
        return Value.ToString("0.####");
    }
}
