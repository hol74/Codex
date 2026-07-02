namespace Finance.Analytics;

public static class PortfolioMath
{
    public static decimal Weight(decimal componentValue, decimal totalValue)
    {
        return totalValue == 0m ? 0m : componentValue / totalValue;
    }
}
