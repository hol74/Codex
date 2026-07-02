using Finance.Application.Portfolios;
using Finance.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace Finance.Infrastructure.Services;

public sealed class PortfolioDashboardService(FinanceDbContext dbContext) : IPortfolioDashboardService
{
    public async Task<DashboardSnapshot> GetSnapshotAsync(CancellationToken cancellationToken = default)
    {
        var portfolio = await dbContext.Portfolios
            .AsNoTracking()
            .Include(x => x.Owner)
            .Include(x => x.BaseCurrency)
            .OrderBy(x => x.Name)
            .FirstAsync(cancellationToken);

        var allocations = await dbContext.TargetAllocations
            .AsNoTracking()
            .Include(x => x.AssetClass)
            .Where(x => x.PortfolioId == portfolio.Id)
            .OrderByDescending(x => x.TargetWeight)
            .Select(x => new DashboardAllocation(
                x.AssetClass!.Name,
                x.TargetWeight,
                x.MinimumWeight,
                x.MaximumWeight))
            .ToListAsync(cancellationToken);

        var regime = await dbContext.RegimeObservations
            .AsNoTracking()
            .OrderByDescending(x => x.ObservationDate)
            .FirstAsync(cancellationToken);

        var proposal = await dbContext.AllocationProposals
            .AsNoTracking()
            .OrderByDescending(x => x.ProposalDate)
            .FirstAsync(cancellationToken);

        var recommendations = await dbContext.RebalanceRecommendations
            .AsNoTracking()
            .Include(x => x.AssetClass)
            .Where(x => x.AllocationProposalId == proposal.Id)
            .OrderByDescending(x => x.TargetWeight)
            .Select(x => new DashboardRecommendation(
                x.AssetClass!.Name,
                x.Action.ToString(),
                x.CurrentWeight,
                x.TargetWeight,
                x.TradeAmountBase))
            .ToListAsync(cancellationToken);

        return new DashboardSnapshot(
            portfolio.Owner!.DisplayName,
            portfolio.Name,
            portfolio.BaseCurrency!.Code,
            await dbContext.Portfolios.CountAsync(cancellationToken),
            await dbContext.Accounts.CountAsync(cancellationToken),
            await dbContext.Instruments.CountAsync(cancellationToken),
            regime.Regime.ToString(),
            regime.Probability,
            allocations,
            recommendations);
    }
}
