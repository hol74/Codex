using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Ports;

public interface IRegimeRunStore
{
    Task SaveAsync(RegimeSnapshot snapshot, CancellationToken cancellationToken = default);
}
