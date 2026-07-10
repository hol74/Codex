namespace MacroRegime.Domain.Allocations;

public sealed record AllocationBand
{
    public AllocationBand(
        AssetClass assetClass,
        AllocationWeight minimum,
        AllocationWeight strategic,
        AllocationWeight maximum)
    {
        if (minimum.Value > strategic.Value)
        {
            throw new ArgumentException("Minimum allocation cannot exceed strategic allocation.", nameof(minimum));
        }

        if (strategic.Value > maximum.Value)
        {
            throw new ArgumentException("Strategic allocation cannot exceed maximum allocation.", nameof(strategic));
        }

        AssetClass = assetClass;
        Minimum = minimum;
        Strategic = strategic;
        Maximum = maximum;
    }

    public AssetClass AssetClass { get; }

    public AllocationWeight Minimum { get; }

    public AllocationWeight Strategic { get; }

    public AllocationWeight Maximum { get; }
}
