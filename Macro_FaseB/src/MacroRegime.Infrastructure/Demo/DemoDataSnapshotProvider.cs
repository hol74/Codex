using MacroRegime.Application.Ports;
using MacroRegime.Application.Regimes;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Demo;

public sealed class DemoDataSnapshotProvider : IDataSnapshotProvider, IDataSnapshotSourceInfoProvider
{
    public DataSnapshotSourceInfo LastSourceInfo { get; private set; } = DataSnapshotSourceInfo.Demo();

    public Task<DataSnapshot?> GetSnapshotAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        LastSourceInfo = DataSnapshotSourceInfo.Demo();
        return Task.FromResult<DataSnapshot?>(DemoMacroRegimeInputs.CreateGoldilocksDataSnapshot(asOfDate));
    }
}
