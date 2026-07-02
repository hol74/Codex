using Finance.Application.PhaseOne;
using Finance.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace Finance.Infrastructure.Services;

public sealed class PhaseOneReadService(FinanceDbContext dbContext) : IPhaseOneReadService
{
    public async Task<IReadOnlyList<PortfolioListItem>> GetPortfoliosAsync(CancellationToken cancellationToken = default)
    {
        return await dbContext.Portfolios
            .AsNoTracking()
            .Include(x => x.Owner)
            .Include(x => x.BaseCurrency)
            .Include(x => x.Accounts)
            .Include(x => x.TargetAllocations)
            .OrderBy(x => x.Name)
            .Select(x => new PortfolioListItem(
                x.Id,
                x.Name,
                x.Owner!.DisplayName,
                x.BaseCurrency!.Code,
                x.Accounts.Count,
                x.TargetAllocations.Count))
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<InstrumentListItem>> GetInstrumentsAsync(CancellationToken cancellationToken = default)
    {
        return await dbContext.Instruments
            .AsNoTracking()
            .Include(x => x.AssetClass)
            .Include(x => x.Currency)
            .OrderBy(x => x.AssetClass!.Name)
            .ThenBy(x => x.Symbol)
            .Select(x => new InstrumentListItem(
                x.Id,
                x.Symbol,
                x.Name,
                x.Type.ToString(),
                x.AssetClass!.Name,
                x.Currency!.Code,
                x.Exchange,
                x.Isin))
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<TransactionListItem>> GetTransactionsAsync(CancellationToken cancellationToken = default)
    {
        return await dbContext.Transactions
            .AsNoTracking()
            .Include(x => x.Portfolio)
            .Include(x => x.Instrument)
            .Include(x => x.PriceCurrency)
            .Include(x => x.CashAccount)
            .Include(x => x.SecuritiesAccount)
            .OrderByDescending(x => x.TradeDate)
            .Select(x => new TransactionListItem(
                x.Id,
                x.TradeDate,
                x.Type.ToString(),
                x.Portfolio!.Name,
                x.Instrument != null ? x.Instrument.Symbol : null,
                x.Quantity,
                x.Price,
                x.GrossAmount,
                x.Fees,
                x.Taxes,
                x.PriceCurrency!.Code,
                x.CashAccount!.Name,
                x.SecuritiesAccount != null ? x.SecuritiesAccount.Name : null,
                x.Notes))
            .ToListAsync(cancellationToken);
    }
}
