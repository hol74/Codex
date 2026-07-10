namespace MacroRegime.Domain.Allocations;

public sealed record PortfolioWeight
{
    public PortfolioWeight(AssetClass assetClass, AllocationWeight weight)
    {
        AssetClass = assetClass;
        Weight = weight;
    }

    public AssetClass AssetClass { get; }

    public AllocationWeight Weight { get; }
}
