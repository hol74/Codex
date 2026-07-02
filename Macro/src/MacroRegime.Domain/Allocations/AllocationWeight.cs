namespace MacroRegime.Domain.Allocations;

public readonly record struct AllocationWeight
{
    public static readonly AllocationWeight Zero = new(0m);
    public static readonly AllocationWeight One = new(1m);

    public AllocationWeight(decimal value)
    {
        if (value is < 0m or > 1m)
        {
            throw new ArgumentOutOfRangeException(nameof(value), "Allocation weight must be between 0 and 1.");
        }

        Value = value;
    }

    public decimal Value { get; }

    public override string ToString()
    {
        return Value.ToString("0.####");
    }
}
