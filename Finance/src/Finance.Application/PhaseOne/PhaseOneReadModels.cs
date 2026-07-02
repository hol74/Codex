namespace Finance.Application.PhaseOne;

public sealed record PortfolioListItem(
    Guid Id,
    string Name,
    string OwnerName,
    string BaseCurrencyCode,
    int AccountCount,
    int TargetAllocationCount);

public sealed record InstrumentListItem(
    Guid Id,
    string Symbol,
    string Name,
    string Type,
    string AssetClass,
    string CurrencyCode,
    string? Exchange,
    string? Isin);

public sealed record TransactionListItem(
    Guid Id,
    DateOnly TradeDate,
    string Type,
    string PortfolioName,
    string? InstrumentSymbol,
    decimal Quantity,
    decimal Price,
    decimal GrossAmount,
    decimal Fees,
    decimal Taxes,
    string CurrencyCode,
    string CashAccountName,
    string? SecuritiesAccountName,
    string? Notes);
