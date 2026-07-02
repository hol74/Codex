namespace MacroRegime.Domain.Common;

public readonly record struct NormalizedScore
{
    public static readonly NormalizedScore Neutral = new(0.5m);

    public NormalizedScore(decimal value)
    {
        if (value is < 0m or > 1m)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "Normalized score must be between 0 and 1.");
        }

        Value = value;
    }

    public decimal Value { get; }

    public bool IsNeutral => Value == Neutral.Value;

    public override string ToString()
    {
        return Value.ToString("0.####");
    }
}
