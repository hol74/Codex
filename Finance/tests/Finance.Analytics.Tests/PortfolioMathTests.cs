using Finance.Analytics;

namespace Finance.Analytics.Tests;

public class PortfolioMathTests
{
    [Fact]
    public void Weight_ReturnsZero_WhenTotalValueIsZero()
    {
        Assert.Equal(0m, PortfolioMath.Weight(100m, 0m));
    }

    [Fact]
    public void Weight_ReturnsComponentShare()
    {
        Assert.Equal(0.25m, PortfolioMath.Weight(25m, 100m));
    }
}
