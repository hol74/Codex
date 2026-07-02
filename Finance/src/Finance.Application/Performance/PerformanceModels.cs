namespace Finance.Application.Performance;

public sealed record PerformanceDashboard(
    Guid PortfolioId,
    string PortfolioName,
    string BaseCurrencyCode,
    DateOnly FromDate,
    DateOnly ToDate,
    decimal MarketValueBase,
    decimal InvestedCapitalBase,
    decimal RealizedProfitLossBase,
    decimal UnrealizedProfitLossBase,
    decimal Twr,
    decimal? Xirr,
    IReadOnlyList<PerformancePoint> ValueSeries,
    IReadOnlyList<PerformancePoint> ReturnSeries,
    IReadOnlyList<AllocationPoint> Allocation,
    IReadOnlyList<PriceHistoryPoint> PriceHistory,
    IReadOnlyList<FxHistoryPoint> FxHistory,
    IReadOnlyList<SnapshotRow> SnapshotRows);

public sealed record PerformancePoint(DateOnly Date, decimal Value);

public sealed record AllocationPoint(string Label, decimal MarketValueBase, decimal Weight);

public sealed record PriceHistoryPoint(string Symbol, DateOnly Date, decimal Close, string CurrencyCode);

public sealed record FxHistoryPoint(DateOnly Date, string FromCurrencyCode, string ToCurrencyCode, decimal Rate);

public sealed record SnapshotRow(
    DateOnly Date,
    decimal MarketValueBase,
    decimal DailyReturn,
    decimal CumulativeReturn,
    decimal ExternalCashFlowBase);
