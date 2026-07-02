using Finance.Application.Performance;
using Finance.Domain.Entities;
using Finance.Domain.Enums;
using Finance.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace Finance.Infrastructure.Services;

public sealed class PerformanceService(FinanceDbContext dbContext) : IPerformanceService
{
    public async Task<PerformanceDashboard?> GetDashboardAsync(CancellationToken cancellationToken = default)
    {
        var portfolio = await dbContext.Portfolios
            .AsNoTracking()
            .Include(x => x.BaseCurrency)
            .OrderBy(x => x.Name)
            .FirstOrDefaultAsync(cancellationToken);

        if (portfolio is null)
        {
            return null;
        }

        var hasSeries = await dbContext.PerformanceSeries
            .AsNoTracking()
            .AnyAsync(x => x.PortfolioId == portfolio.Id, cancellationToken);

        if (!hasSeries)
        {
            await RebuildSnapshotsAsync(cancellationToken);
        }

        var series = await dbContext.PerformanceSeries
            .AsNoTracking()
            .Where(x => x.PortfolioId == portfolio.Id)
            .OrderBy(x => x.Date)
            .ToListAsync(cancellationToken);

        if (series.Count == 0)
        {
            return null;
        }

        var latestDate = series[^1].Date;
        var latestHoldings = await dbContext.HoldingSnapshots
            .AsNoTracking()
            .Include(x => x.Instrument)!.ThenInclude(x => x!.AssetClass)
            .Where(x => x.PortfolioId == portfolio.Id && x.Date == latestDate)
            .ToListAsync(cancellationToken);

        var cashFlows = await dbContext.CashFlows
            .AsNoTracking()
            .Where(x => x.PortfolioId == portfolio.Id)
            .OrderBy(x => x.Date)
            .ToListAsync(cancellationToken);

        var priceHistory = await dbContext.Prices
            .AsNoTracking()
            .Include(x => x.Instrument)
            .Include(x => x.Currency)
            .OrderBy(x => x.Instrument!.Symbol)
            .ThenBy(x => x.Date)
            .Select(x => new PriceHistoryPoint(x.Instrument!.Symbol, x.Date, x.Close, x.Currency!.Code))
            .ToListAsync(cancellationToken);

        var fxHistory = await dbContext.FxRates
            .AsNoTracking()
            .Include(x => x.FromCurrency)
            .Include(x => x.ToCurrency)
            .OrderBy(x => x.Date)
            .Select(x => new FxHistoryPoint(x.Date, x.FromCurrency!.Code, x.ToCurrency!.Code, x.Rate))
            .ToListAsync(cancellationToken);

        var allocation = latestHoldings
            .Where(x => x.MarketValueBase != 0m)
            .GroupBy(x => x.Instrument is null ? "Liquidita" : x.Instrument.AssetClass?.Name ?? "Altro")
            .Select(group => new AllocationPoint(group.Key, group.Sum(x => x.MarketValueBase), 0m))
            .OrderByDescending(x => x.MarketValueBase)
            .ToList();

        var total = allocation.Sum(x => x.MarketValueBase);
        allocation = allocation
            .Select(x => x with { Weight = total == 0m ? 0m : x.MarketValueBase / total })
            .ToList();

        var marketValue = series[^1].MarketValueBase;
        var realizedProfitLoss = await CalculateRealizedProfitLossAsync(portfolio.Id, cancellationToken);
        var unrealizedProfitLoss = latestHoldings.Sum(x => x.UnrealizedProfitLossBase);
        var investedCapital = cashFlows.Sum(x => x.Amount);
        var xirr = CalculateXirr(cashFlows, marketValue, latestDate);

        return new PerformanceDashboard(
            portfolio.Id,
            portfolio.Name,
            portfolio.BaseCurrency?.Code ?? "-",
            series[0].Date,
            latestDate,
            marketValue,
            investedCapital,
            realizedProfitLoss,
            unrealizedProfitLoss,
            series[^1].CumulativeReturn,
            xirr,
            series.Select(x => new PerformancePoint(x.Date, x.MarketValueBase)).ToList(),
            series.Select(x => new PerformancePoint(x.Date, x.DailyReturn)).ToList(),
            allocation,
            priceHistory,
            fxHistory,
            series
                .OrderByDescending(x => x.Date)
                .Take(10)
                .Select(x => new SnapshotRow(x.Date, x.MarketValueBase, x.DailyReturn, x.CumulativeReturn, x.ExternalCashFlowBase))
                .ToList());
    }

    public async Task RebuildSnapshotsAsync(CancellationToken cancellationToken = default)
    {
        var portfolio = await dbContext.Portfolios
            .Include(x => x.BaseCurrency)
            .OrderBy(x => x.Name)
            .FirstOrDefaultAsync(cancellationToken);

        if (portfolio is null)
        {
            return;
        }

        var transactions = await dbContext.Transactions
            .AsNoTracking()
            .Include(x => x.Instrument)!.ThenInclude(x => x!.Currency)
            .Include(x => x.Instrument)!.ThenInclude(x => x!.AssetClass)
            .Include(x => x.CashAccount)!.ThenInclude(x => x!.Currency)
            .Where(x => x.PortfolioId == portfolio.Id)
            .OrderBy(x => x.TradeDate)
            .ToListAsync(cancellationToken);

        transactions = transactions
            .OrderBy(x => x.TradeDate)
            .ThenBy(x => x.CreatedAt)
            .ToList();

        if (transactions.Count == 0)
        {
            return;
        }

        var fromDate = transactions[0].TradeDate;
        var today = DateOnly.FromDateTime(DateTime.Today);
        var lastPriceDate = await dbContext.Prices
            .AsNoTracking()
            .OrderByDescending(x => x.Date)
            .Select(x => (DateOnly?)x.Date)
            .FirstOrDefaultAsync(cancellationToken);
        var toDate = lastPriceDate is not null && lastPriceDate > today ? lastPriceDate.Value : today;

        var prices = await dbContext.Prices
            .AsNoTracking()
            .Where(x => x.Date <= toDate)
            .OrderBy(x => x.Date)
            .ToListAsync(cancellationToken);

        var fxRates = await dbContext.FxRates
            .AsNoTracking()
            .Where(x => x.Date <= toDate)
            .OrderBy(x => x.Date)
            .ToListAsync(cancellationToken);

        var priceByInstrument = prices
            .GroupBy(x => x.InstrumentId)
            .ToDictionary(x => x.Key, x => x.OrderBy(p => p.Date).ToList());

        var existingHoldings = await dbContext.HoldingSnapshots
            .Where(x => x.PortfolioId == portfolio.Id)
            .ToListAsync(cancellationToken);
        var existingSeries = await dbContext.PerformanceSeries
            .Where(x => x.PortfolioId == portfolio.Id)
            .ToListAsync(cancellationToken);
        var existingFlows = await dbContext.CashFlows
            .Where(x => x.PortfolioId == portfolio.Id)
            .ToListAsync(cancellationToken);

        dbContext.HoldingSnapshots.RemoveRange(existingHoldings);
        dbContext.PerformanceSeries.RemoveRange(existingSeries);
        dbContext.CashFlows.RemoveRange(existingFlows);

        var positions = new Dictionary<Guid, PositionState>();
        var cashBalances = new Dictionary<Guid, CashState>();
        var series = new List<PerformanceSeries>();
        var snapshots = new List<HoldingSnapshot>();
        var cashFlows = new List<CashFlow>();
        var cumulativeGrowth = 1m;
        decimal previousMarketValue = 0m;

        for (var date = fromDate; date <= toDate; date = date.AddDays(1))
        {
            var todaysTransactions = transactions.Where(x => x.TradeDate == date).ToList();
            var externalFlow = 0m;

            foreach (var transaction in todaysTransactions)
            {
                ApplyTransaction(transaction, positions, cashBalances);

                if (transaction.Type is TransactionType.Deposit or TransactionType.Withdrawal)
                {
                    var amount = transaction.GrossAmount * transaction.FxRateToBase;
                    externalFlow += amount;
                    cashFlows.Add(new CashFlow
                    {
                        PortfolioId = portfolio.Id,
                        AccountId = transaction.CashAccountId,
                        Date = transaction.TradeDate,
                        Type = transaction.Type,
                        Amount = amount,
                        CurrencyId = transaction.PriceCurrencyId,
                        IsExternalFlow = true
                    });
                }
            }

            var instrumentMarketValue = 0m;
            foreach (var position in positions.Values.Where(x => x.Quantity != 0m))
            {
                var price = GetLatestPrice(position.InstrumentId, date, priceByInstrument) ?? position.LastTradePrice;
                var fx = GetFxRate(position.CurrencyId, portfolio.BaseCurrencyId, date, fxRates);
                var marketValue = position.Quantity * price * fx;
                instrumentMarketValue += marketValue;

                snapshots.Add(new HoldingSnapshot
                {
                    PortfolioId = portfolio.Id,
                    AccountId = position.AccountId,
                    InstrumentId = position.InstrumentId,
                    Date = date,
                    Quantity = position.Quantity,
                    MarketValueBase = marketValue,
                    CostBasisBase = position.CostBasisBase,
                    UnrealizedProfitLossBase = marketValue - position.CostBasisBase
                });
            }

            var cashMarketValue = 0m;
            foreach (var cash in cashBalances.Values.Where(x => x.Balance != 0m))
            {
                var fx = GetFxRate(cash.CurrencyId, portfolio.BaseCurrencyId, date, fxRates);
                var marketValue = cash.Balance * fx;
                cashMarketValue += marketValue;

                snapshots.Add(new HoldingSnapshot
                {
                    PortfolioId = portfolio.Id,
                    AccountId = cash.AccountId,
                    Date = date,
                    Quantity = cash.Balance,
                    MarketValueBase = marketValue,
                    CostBasisBase = marketValue,
                    UnrealizedProfitLossBase = 0m
                });
            }

            var marketValueBase = instrumentMarketValue + cashMarketValue;
            var dailyReturn = previousMarketValue == 0m
                ? 0m
                : (marketValueBase - previousMarketValue - externalFlow) / previousMarketValue;
            cumulativeGrowth *= 1m + dailyReturn;

            series.Add(new PerformanceSeries
            {
                PortfolioId = portfolio.Id,
                Date = date,
                MarketValueBase = marketValueBase,
                DailyReturn = dailyReturn,
                CumulativeReturn = cumulativeGrowth - 1m,
                ExternalCashFlowBase = externalFlow
            });

            previousMarketValue = marketValueBase;
        }

        dbContext.HoldingSnapshots.AddRange(snapshots);
        dbContext.PerformanceSeries.AddRange(series);
        dbContext.CashFlows.AddRange(cashFlows);
        dbContext.AuditEvents.Add(new AuditEvent
        {
            Area = "Performance",
            EventType = "SnapshotsRebuilt",
            Message = $"Rigenerati {series.Count} snapshot giornalieri per {portfolio.Name}.",
            Actor = "system"
        });

        await dbContext.SaveChangesAsync(cancellationToken);
    }

    private async Task<decimal> CalculateRealizedProfitLossAsync(Guid portfolioId, CancellationToken cancellationToken)
    {
        var transactions = await dbContext.Transactions
            .AsNoTracking()
            .Where(x => x.PortfolioId == portfolioId && (x.Type == TransactionType.Buy || x.Type == TransactionType.Sell))
            .OrderBy(x => x.TradeDate)
            .ToListAsync(cancellationToken);

        transactions = transactions
            .OrderBy(x => x.TradeDate)
            .ThenBy(x => x.CreatedAt)
            .ToList();

        var positions = new Dictionary<Guid, PositionState>();
        var cash = new Dictionary<Guid, CashState>();

        foreach (var transaction in transactions)
        {
            ApplyTransaction(transaction, positions, cash);
        }

        return positions.Values.Sum(x => x.RealizedProfitLossBase);
    }

    private static void ApplyTransaction(
        Transaction transaction,
        Dictionary<Guid, PositionState> positions,
        Dictionary<Guid, CashState> cashBalances)
    {
        var cashState = GetCashState(transaction, cashBalances);
        cashState.Balance += transaction.GrossAmount - transaction.Fees - transaction.Taxes;

        if (transaction.Type is not (TransactionType.Buy or TransactionType.Sell) || transaction.InstrumentId is null)
        {
            return;
        }

        var position = GetPositionState(transaction, positions);
        position.LastTradePrice = transaction.Price;

        if (transaction.Type == TransactionType.Buy)
        {
            var cost = (Math.Abs(transaction.GrossAmount) + transaction.Fees + transaction.Taxes) * transaction.FxRateToBase;
            position.Quantity += transaction.Quantity;
            position.CostBasisBase += cost;
            return;
        }

        var soldQuantity = Math.Min(transaction.Quantity, position.Quantity);
        var averageCost = position.Quantity == 0m ? 0m : position.CostBasisBase / position.Quantity;
        var releasedCost = averageCost * soldQuantity;
        var proceeds = (transaction.GrossAmount - transaction.Fees - transaction.Taxes) * transaction.FxRateToBase;

        position.Quantity -= soldQuantity;
        position.CostBasisBase -= releasedCost;
        position.RealizedProfitLossBase += proceeds - releasedCost;
    }

    private static CashState GetCashState(Transaction transaction, Dictionary<Guid, CashState> cashBalances)
    {
        if (cashBalances.TryGetValue(transaction.CashAccountId, out var cash))
        {
            return cash;
        }

        cash = new CashState(transaction.CashAccountId, transaction.CashAccount?.CurrencyId ?? transaction.PriceCurrencyId);
        cashBalances[transaction.CashAccountId] = cash;
        return cash;
    }

    private static PositionState GetPositionState(Transaction transaction, Dictionary<Guid, PositionState> positions)
    {
        var instrumentId = transaction.InstrumentId!.Value;
        if (positions.TryGetValue(instrumentId, out var position))
        {
            return position;
        }

        position = new PositionState(
            instrumentId,
            transaction.SecuritiesAccountId,
            transaction.Instrument?.CurrencyId ?? transaction.PriceCurrencyId,
            transaction.Price);
        positions[instrumentId] = position;
        return position;
    }

    private static decimal? GetLatestPrice(Guid instrumentId, DateOnly date, IReadOnlyDictionary<Guid, List<Price>> prices)
    {
        if (!prices.TryGetValue(instrumentId, out var instrumentPrices))
        {
            return null;
        }

        return instrumentPrices.LastOrDefault(x => x.Date <= date)?.Close;
    }

    private static decimal GetFxRate(Guid fromCurrencyId, Guid toCurrencyId, DateOnly date, IReadOnlyList<FxRate> fxRates)
    {
        if (fromCurrencyId == toCurrencyId)
        {
            return 1m;
        }

        var direct = fxRates
            .LastOrDefault(x => x.FromCurrencyId == fromCurrencyId && x.ToCurrencyId == toCurrencyId && x.Date <= date);
        if (direct is not null)
        {
            return direct.Rate;
        }

        var inverse = fxRates
            .LastOrDefault(x => x.FromCurrencyId == toCurrencyId && x.ToCurrencyId == fromCurrencyId && x.Date <= date);
        if (inverse is not null && inverse.Rate != 0m)
        {
            return 1m / inverse.Rate;
        }

        return 1m;
    }

    private static decimal? CalculateXirr(IReadOnlyList<CashFlow> cashFlows, decimal finalValue, DateOnly finalDate)
    {
        if (cashFlows.Count == 0 || finalValue <= 0m)
        {
            return null;
        }

        var datedFlows = cashFlows
            .Select(x => (x.Date, Amount: -x.Amount))
            .Append((Date: finalDate, Amount: finalValue))
            .OrderBy(x => x.Date)
            .ToList();

        if (!datedFlows.Any(x => x.Amount < 0m) || !datedFlows.Any(x => x.Amount > 0m))
        {
            return null;
        }

        var low = -0.9999m;
        var high = 10m;
        var lowValue = NetPresentValue(datedFlows, low);
        var highValue = NetPresentValue(datedFlows, high);

        if (Math.Sign(lowValue) == Math.Sign(highValue))
        {
            return null;
        }

        for (var i = 0; i < 100; i++)
        {
            var mid = (low + high) / 2m;
            var midValue = NetPresentValue(datedFlows, mid);

            if (Math.Abs(midValue) < 0.0001m)
            {
                return mid;
            }

            if (Math.Sign(lowValue) == Math.Sign(midValue))
            {
                low = mid;
                lowValue = midValue;
            }
            else
            {
                high = mid;
            }
        }

        return (low + high) / 2m;
    }

    private static decimal NetPresentValue(IReadOnlyList<(DateOnly Date, decimal Amount)> cashFlows, decimal rate)
    {
        var startDate = cashFlows[0].Date;
        var total = 0d;
        var rateDouble = (double)(1m + rate);

        foreach (var cashFlow in cashFlows)
        {
            var years = (cashFlow.Date.DayNumber - startDate.DayNumber) / 365d;
            total += (double)cashFlow.Amount / Math.Pow(rateDouble, years);
        }

        return (decimal)total;
    }

    private sealed class PositionState(Guid instrumentId, Guid? accountId, Guid currencyId, decimal lastTradePrice)
    {
        public Guid InstrumentId { get; } = instrumentId;
        public Guid? AccountId { get; } = accountId;
        public Guid CurrencyId { get; } = currencyId;
        public decimal LastTradePrice { get; set; } = lastTradePrice;
        public decimal Quantity { get; set; }
        public decimal CostBasisBase { get; set; }
        public decimal RealizedProfitLossBase { get; set; }
    }

    private sealed class CashState(Guid accountId, Guid currencyId)
    {
        public Guid AccountId { get; } = accountId;
        public Guid CurrencyId { get; } = currencyId;
        public decimal Balance { get; set; }
    }
}
