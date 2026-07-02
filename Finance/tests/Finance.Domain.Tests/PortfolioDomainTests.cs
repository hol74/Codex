using Finance.Domain.Entities;

namespace Finance.Domain.Tests;

public class PortfolioDomainTests
{
    [Fact]
    public void TargetAllocation_CanRepresentPolicyBand()
    {
        var allocation = new TargetAllocation
        {
            TargetWeight = 0.60m,
            MinimumWeight = 0.50m,
            MaximumWeight = 0.70m
        };

        Assert.True(allocation.MinimumWeight < allocation.TargetWeight);
        Assert.True(allocation.TargetWeight < allocation.MaximumWeight);
    }
}
