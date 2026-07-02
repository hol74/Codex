using System.ComponentModel.DataAnnotations;
using Finance.Domain.Enums;

namespace Finance.Application.Ledger;

public sealed record LookupItem(Guid Id, string Label);

public sealed record TransactionTypeItem(TransactionType Value, string Label);

public sealed record InstrumentTypeItem(InstrumentType Value, string Label);

public sealed record TransactionFormOptions(
    IReadOnlyList<LookupItem> Portfolios,
    IReadOnlyList<LookupItem> CashAccounts,
    IReadOnlyList<LookupItem> SecuritiesAccounts,
    IReadOnlyList<LookupItem> Instruments,
    IReadOnlyList<LookupItem> Currencies,
    IReadOnlyList<TransactionTypeItem> TransactionTypes);

public sealed class TransactionEditModel
{
    public Guid? Id { get; set; }

    [Required]
    public DateTime TradeDate { get; set; } = DateTime.Today;

    public DateTime? SettlementDate { get; set; }

    [Required]
    public TransactionType Type { get; set; } = TransactionType.Buy;

    [Required]
    public Guid PortfolioId { get; set; }

    public Guid? InstrumentId { get; set; }

    [Required]
    public Guid CashAccountId { get; set; }

    public Guid? SecuritiesAccountId { get; set; }

    [Range(0, double.MaxValue)]
    public decimal Quantity { get; set; }

    [Range(0, double.MaxValue)]
    public decimal Price { get; set; } = 1m;

    [Required]
    public Guid PriceCurrencyId { get; set; }

    public decimal GrossAmount { get; set; }

    [Range(0, double.MaxValue)]
    public decimal Fees { get; set; }

    [Range(0, double.MaxValue)]
    public decimal Taxes { get; set; }

    [Range(0.000001, double.MaxValue)]
    public decimal FxRateToBase { get; set; } = 1m;

    public string? Notes { get; set; }
    public string? ImportSource { get; set; }
    public string? BrokerTransactionId { get; set; }
}

public sealed record TransactionFormPage(TransactionEditModel Transaction, TransactionFormOptions Options);

public sealed record LedgerTransactionListItem(
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

public sealed record InstrumentPositionItem(
    string Symbol,
    string Name,
    string AssetClass,
    decimal Quantity,
    decimal LastPrice,
    decimal MarketValueBase,
    decimal CostBasisBase,
    decimal UnrealizedProfitLossBase);

public sealed record CashBalanceItem(
    string AccountName,
    string CurrencyCode,
    decimal Balance);

public sealed record CurrentPositionsSnapshot(
    IReadOnlyList<InstrumentPositionItem> Instruments,
    IReadOnlyList<CashBalanceItem> CashBalances,
    decimal TotalMarketValueBase,
    decimal TotalCashBalance);

public sealed record AuditEventListItem(
    DateTimeOffset CreatedAt,
    string Area,
    string EventType,
    string Message,
    string? Actor);

public sealed record InstrumentFormOptions(
    IReadOnlyList<LookupItem> Currencies,
    IReadOnlyList<LookupItem> AssetClasses,
    IReadOnlyList<InstrumentTypeItem> InstrumentTypes);

public sealed class InstrumentEditModel
{
    public Guid? Id { get; set; }

    [Required]
    [StringLength(160)]
    public string Name { get; set; } = string.Empty;

    [Required]
    [StringLength(32)]
    public string Symbol { get; set; } = string.Empty;

    [StringLength(12)]
    public string? Isin { get; set; }

    [StringLength(32)]
    public string? Exchange { get; set; }

    [Required]
    public InstrumentType Type { get; set; } = InstrumentType.Etf;

    [Required]
    public Guid CurrencyId { get; set; }

    [Required]
    public Guid AssetClassId { get; set; }
}

public sealed record InstrumentFormPage(InstrumentEditModel Instrument, InstrumentFormOptions Options);
