using MacroRegime.Application.Runs;

namespace MacroRegime.Application.Ports;

public interface IRegimeRunStore
{
    Task<string> SaveAsync(RegimeRunDocument document, CancellationToken cancellationToken = default);

    Task<RegimeRunDocument?> LoadAsync(DateOnly asOfDate, CancellationToken cancellationToken = default);
}
