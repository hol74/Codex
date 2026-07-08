using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Ports;

public interface IRegimeRunStore
{
    Task<string> SaveAsync(RegimeSnapshot snapshot, CancellationToken cancellationToken = default);
}
