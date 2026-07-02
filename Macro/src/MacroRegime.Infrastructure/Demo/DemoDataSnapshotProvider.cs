using MacroRegime.Application.Ports;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Demo;

public sealed class DemoDataSnapshotProvider : IDataSnapshotProvider
{
    public Task<DataSnapshot?> GetSnapshotAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        return Task.FromResult<DataSnapshot?>(DemoMacroRegimeInputs.CreateGoldilocksDataSnapshot(asOfDate));
    }
}
