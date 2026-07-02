using Finance.Application.Portfolios;

namespace Finance.Application.Tests;

public class DashboardSnapshotTests
{
    [Fact]
    public void DashboardSnapshot_StoresPortfolioSummary()
    {
        var snapshot = new DashboardSnapshot(
            "Owner",
            "Portfolio",
            "EUR",
            1,
            2,
            3,
            "UncertainTransition",
            0.58m,
            [],
            []);

        Assert.Equal("Portfolio", snapshot.PortfolioName);
        Assert.Equal("EUR", snapshot.BaseCurrencyCode);
        Assert.Equal(3, snapshot.InstrumentCount);
    }
}
