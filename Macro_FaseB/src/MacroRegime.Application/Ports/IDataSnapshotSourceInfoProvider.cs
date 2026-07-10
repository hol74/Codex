using MacroRegime.Application.Regimes;

namespace MacroRegime.Application.Ports;

public interface IDataSnapshotSourceInfoProvider
{
    DataSnapshotSourceInfo LastSourceInfo { get; }
}
