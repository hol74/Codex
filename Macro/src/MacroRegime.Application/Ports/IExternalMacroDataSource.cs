using MacroRegime.Application.External;

namespace MacroRegime.Application.Ports;

public interface IExternalMacroDataSource
{
    Task<IReadOnlyList<FredObservation>> FetchAsync(FredFetchCommand command, CancellationToken cancellationToken = default);
}
