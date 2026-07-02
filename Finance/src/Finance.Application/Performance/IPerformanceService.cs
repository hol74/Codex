namespace Finance.Application.Performance;

public interface IPerformanceService
{
    Task<PerformanceDashboard?> GetDashboardAsync(CancellationToken cancellationToken = default);

    Task RebuildSnapshotsAsync(CancellationToken cancellationToken = default);
}
