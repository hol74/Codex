namespace Finance.Application.PhaseOne;

public interface IPhaseOneReadService
{
    Task<IReadOnlyList<PortfolioListItem>> GetPortfoliosAsync(CancellationToken cancellationToken = default);
    Task<IReadOnlyList<InstrumentListItem>> GetInstrumentsAsync(CancellationToken cancellationToken = default);
    Task<IReadOnlyList<TransactionListItem>> GetTransactionsAsync(CancellationToken cancellationToken = default);
}
