using MacroRegime.Domain.Allocations;

namespace MacroRegime.Domain.Tests.Allocations;

public sealed class AllocationPolicyTests
{
    [Fact]
    public void AllocationWeight_RejectsValuesOutsideZeroAndOne()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new AllocationWeight(-0.01m));
        Assert.Throws<ArgumentOutOfRangeException>(() => new AllocationWeight(1.01m));
    }

    [Fact]
    public void AllocationBand_RequiresStrategicWeightInsideBand()
    {
        Assert.Throws<ArgumentException>(() => new AllocationBand(
            AssetClass.GlobalEquity,
            new AllocationWeight(0.60m),
            new AllocationWeight(0.50m),
            new AllocationWeight(0.80m)));

        Assert.Throws<ArgumentException>(() => new AllocationBand(
            AssetClass.GlobalEquity,
            new AllocationWeight(0.40m),
            new AllocationWeight(0.90m),
            new AllocationWeight(0.80m)));
    }

    [Fact]
    public void StrategicAllocationPolicy_RejectsStrategicWeightsThatDoNotSumToOne()
    {
        var bands = new[]
        {
            new AllocationBand(AssetClass.Cash, new AllocationWeight(0m), new AllocationWeight(0.10m), new AllocationWeight(0.30m)),
            new AllocationBand(AssetClass.GlobalEquity, new AllocationWeight(0.30m), new AllocationWeight(0.50m), new AllocationWeight(0.80m))
        };

        Assert.Throws<ArgumentException>(() => new StrategicAllocationPolicy(
            "Invalid",
            bands,
            new AllocationWeight(0.10m),
            0.001m));
    }

    [Fact]
    public void CurrentPortfolio_RejectsDuplicateAssetClassesAndUnnormalizedWeights()
    {
        Assert.Throws<ArgumentException>(() => new CurrentPortfolio(new[]
        {
            new PortfolioWeight(AssetClass.Cash, new AllocationWeight(0.10m)),
            new PortfolioWeight(AssetClass.Cash, new AllocationWeight(0.90m))
        }));

        Assert.Throws<ArgumentException>(() => new CurrentPortfolio(new[]
        {
            new PortfolioWeight(AssetClass.Cash, new AllocationWeight(0.10m)),
            new PortfolioWeight(AssetClass.GlobalEquity, new AllocationWeight(0.70m))
        }));
    }
}
