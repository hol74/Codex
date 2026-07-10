using MacroRegime.Application.External;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Ports;

public interface IMarketDataFileWriter
{
    Task<string> WriteAsync(IReadOnlyList<MarketDataObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken cancellationToken = default);
}
