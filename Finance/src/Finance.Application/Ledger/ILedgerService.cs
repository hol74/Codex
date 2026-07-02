namespace Finance.Application.Ledger;

using Finance.Domain.Enums;

public interface ILedgerService
{
    Task<IReadOnlyList<LedgerTransactionListItem>> GetTransactionsAsync(CancellationToken cancellationToken = default);
    Task<IReadOnlyList<LedgerTransactionListItem>> GetTransactionsAsync(TransactionType type, CancellationToken cancellationToken = default);
    Task<TransactionFormPage> NewTransactionAsync(CancellationToken cancellationToken = default);
    Task<TransactionFormPage> NewTransactionAsync(TransactionType type, CancellationToken cancellationToken = default);
    Task<TransactionFormPage?> GetTransactionForEditAsync(Guid id, CancellationToken cancellationToken = default);
    Task<Guid> CreateTransactionAsync(TransactionEditModel model, CancellationToken cancellationToken = default);
    Task<bool> UpdateTransactionAsync(TransactionEditModel model, CancellationToken cancellationToken = default);
    Task<LedgerTransactionListItem?> GetTransactionForDeleteAsync(Guid id, CancellationToken cancellationToken = default);
    Task<bool> DeleteTransactionAsync(Guid id, CancellationToken cancellationToken = default);
    Task<CurrentPositionsSnapshot> GetCurrentPositionsAsync(CancellationToken cancellationToken = default);
    Task<IReadOnlyList<AuditEventListItem>> GetAuditEventsAsync(CancellationToken cancellationToken = default);
    Task<InstrumentFormPage> NewInstrumentAsync(CancellationToken cancellationToken = default);
    Task<InstrumentFormPage?> GetInstrumentForEditAsync(Guid id, CancellationToken cancellationToken = default);
    Task<Guid> CreateInstrumentAsync(InstrumentEditModel model, CancellationToken cancellationToken = default);
    Task<bool> UpdateInstrumentAsync(InstrumentEditModel model, CancellationToken cancellationToken = default);
    Task<InstrumentEditModel?> GetInstrumentForDeleteAsync(Guid id, CancellationToken cancellationToken = default);
    Task<bool> DeleteInstrumentAsync(Guid id, CancellationToken cancellationToken = default);
}
