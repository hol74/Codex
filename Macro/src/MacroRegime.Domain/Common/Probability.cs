namespace MacroRegime.Domain.Common;

public readonly record struct Probability
{
    public static readonly Probability Zero = new(0m);
    public static readonly Probability One = new(1m);

    public Probability(decimal value)
    {
        if (value is < 0m or > 1m)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "Probability must be between 0 and 1.");
        }

        Value = value;
    }

    public decimal Value { get; }

    public override string ToString()
    {
        return Value.ToString("0.####");
    }
}
