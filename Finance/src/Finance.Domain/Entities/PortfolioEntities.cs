using Finance.Domain.Common;
using Finance.Domain.Enums;

namespace Finance.Domain.Entities;

public sealed class Owner : Entity
{
    public required string DisplayName { get; set; }
    public string? Email { get; set; }
    public ICollection<Portfolio> Portfolios { get; set; } = [];
}

public sealed class Currency : Entity
{
    public required string Code { get; set; }
    public required string Name { get; set; }
    public string? Symbol { get; set; }
}

public sealed class AssetClass : Entity
{
    public required string Code { get; set; }
    public required string Name { get; set; }
    public string? Description { get; set; }
    public Guid? ParentAssetClassId { get; set; }
    public AssetClass? ParentAssetClass { get; set; }
}

public sealed class Portfolio : Entity
{
    public required string Name { get; set; }
    public Guid OwnerId { get; set; }
    public Owner? Owner { get; set; }
    public Guid BaseCurrencyId { get; set; }
    public Currency? BaseCurrency { get; set; }
    public ICollection<Account> Accounts { get; set; } = [];
    public ICollection<TargetAllocation> TargetAllocations { get; set; } = [];
}

public sealed class Account : Entity
{
    public required string Name { get; set; }
    public AccountType Type { get; set; }
    public Guid PortfolioId { get; set; }
    public Portfolio? Portfolio { get; set; }
    public Guid CurrencyId { get; set; }
    public Currency? Currency { get; set; }
    public string? BrokerName { get; set; }
    public string? ExternalAccountId { get; set; }
}

public sealed class Instrument : Entity
{
    public required string Name { get; set; }
    public required string Symbol { get; set; }
    public string? Isin { get; set; }
    public string? Exchange { get; set; }
    public InstrumentType Type { get; set; }
    public Guid CurrencyId { get; set; }
    public Currency? Currency { get; set; }
    public Guid AssetClassId { get; set; }
    public AssetClass? AssetClass { get; set; }
}

public sealed class Transaction : Entity
{
    public DateOnly TradeDate { get; set; }
    public DateOnly? SettlementDate { get; set; }
    public TransactionType Type { get; set; }
    public Guid PortfolioId { get; set; }
    public Portfolio? Portfolio { get; set; }
    public Guid? InstrumentId { get; set; }
    public Instrument? Instrument { get; set; }
    public Guid CashAccountId { get; set; }
    public Account? CashAccount { get; set; }
    public Guid? SecuritiesAccountId { get; set; }
    public Account? SecuritiesAccount { get; set; }
    public decimal Quantity { get; set; }
    public decimal Price { get; set; }
    public Guid PriceCurrencyId { get; set; }
    public Currency? PriceCurrency { get; set; }
    public decimal GrossAmount { get; set; }
    public decimal Fees { get; set; }
    public decimal Taxes { get; set; }
    public decimal FxRateToBase { get; set; } = 1m;
    public string? Notes { get; set; }
    public string? ImportSource { get; set; }
    public string? BrokerTransactionId { get; set; }
}

public sealed class CorporateAction : Entity
{
    public CorporateActionType Type { get; set; }
    public DateOnly EffectiveDate { get; set; }
    public Guid InstrumentId { get; set; }
    public Instrument? Instrument { get; set; }
    public decimal QuantityFactor { get; set; } = 1m;
    public decimal CashAmount { get; set; }
    public Guid? CashCurrencyId { get; set; }
    public Currency? CashCurrency { get; set; }
    public string? Notes { get; set; }
}

public sealed class Price : Entity
{
    public Guid InstrumentId { get; set; }
    public Instrument? Instrument { get; set; }
    public DateOnly Date { get; set; }
    public decimal Close { get; set; }
    public Guid CurrencyId { get; set; }
    public Currency? Currency { get; set; }
    public required string Source { get; set; }
}

public sealed class FxRate : Entity
{
    public DateOnly Date { get; set; }
    public Guid FromCurrencyId { get; set; }
    public Currency? FromCurrency { get; set; }
    public Guid ToCurrencyId { get; set; }
    public Currency? ToCurrency { get; set; }
    public decimal Rate { get; set; }
    public required string Source { get; set; }
}

public sealed class HoldingSnapshot : Entity
{
    public Guid PortfolioId { get; set; }
    public Portfolio? Portfolio { get; set; }
    public Guid? AccountId { get; set; }
    public Account? Account { get; set; }
    public Guid? InstrumentId { get; set; }
    public Instrument? Instrument { get; set; }
    public DateOnly Date { get; set; }
    public decimal Quantity { get; set; }
    public decimal MarketValueBase { get; set; }
    public decimal CostBasisBase { get; set; }
    public decimal UnrealizedProfitLossBase { get; set; }
}

public sealed class CashFlow : Entity
{
    public Guid PortfolioId { get; set; }
    public Portfolio? Portfolio { get; set; }
    public Guid AccountId { get; set; }
    public Account? Account { get; set; }
    public DateOnly Date { get; set; }
    public TransactionType Type { get; set; }
    public decimal Amount { get; set; }
    public Guid CurrencyId { get; set; }
    public Currency? Currency { get; set; }
    public bool IsExternalFlow { get; set; }
}

public sealed class Benchmark : Entity
{
    public required string Name { get; set; }
    public required string Symbol { get; set; }
    public Guid CurrencyId { get; set; }
    public Currency? Currency { get; set; }
}

public sealed class TargetAllocation : Entity
{
    public Guid PortfolioId { get; set; }
    public Portfolio? Portfolio { get; set; }
    public Guid AssetClassId { get; set; }
    public AssetClass? AssetClass { get; set; }
    public decimal TargetWeight { get; set; }
    public decimal MinimumWeight { get; set; }
    public decimal MaximumWeight { get; set; }
}

public sealed class PerformanceSeries : Entity
{
    public Guid PortfolioId { get; set; }
    public Portfolio? Portfolio { get; set; }
    public DateOnly Date { get; set; }
    public decimal MarketValueBase { get; set; }
    public decimal DailyReturn { get; set; }
    public decimal CumulativeReturn { get; set; }
    public decimal ExternalCashFlowBase { get; set; }
}
