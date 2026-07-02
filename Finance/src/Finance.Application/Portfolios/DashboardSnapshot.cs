namespace Finance.Application.Portfolios;

public sealed record DashboardSnapshot(
    string OwnerName,
    string PortfolioName,
    string BaseCurrencyCode,
    int PortfolioCount,
    int AccountCount,
    int InstrumentCount,
    string CurrentRegime,
    decimal RegimeProbability,
    IReadOnlyList<DashboardAllocation> TargetAllocations,
    IReadOnlyList<DashboardRecommendation> RecentRecommendations);

public sealed record DashboardAllocation(
    string AssetClass,
    decimal TargetWeight,
    decimal MinimumWeight,
    decimal MaximumWeight);

public sealed record DashboardRecommendation(
    string AssetClass,
    string Action,
    decimal CurrentWeight,
    decimal TargetWeight,
    decimal TradeAmountBase);
