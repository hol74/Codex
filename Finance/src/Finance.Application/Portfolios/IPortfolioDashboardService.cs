namespace Finance.Application.Portfolios;

public interface IPortfolioDashboardService
{
    Task<DashboardSnapshot> GetSnapshotAsync(CancellationToken cancellationToken = default);
}
