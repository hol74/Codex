using MacroRegime.Application.External;

namespace MacroRegime.Application.Ports;

public interface IExternalMarketDataSource
{
    Task<IReadOnlyList<MarketDataObservation>> FetchAsync(MarketDataFetchCommand command, CancellationToken cancellationToken = default);
}
