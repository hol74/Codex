using MacroRegime.Domain.Data;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Ports;

public interface IDataSnapshotProvider
{
    Task<DataSnapshot?> GetSnapshotAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default);
}
