using System.Security.Cryptography;
using System.Text;
using MacroRegime.Application.External;
using MacroRegime.Application.Ports;

namespace MacroRegime.Infrastructure.External;

public sealed class MarketDataStubDataSource : IExternalMarketDataSource
{
    public Task<IReadOnlyList<MarketDataObservation>> FetchAsync(MarketDataFetchCommand command, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        var asOf = command.AsOfDate.Value;
        var observations = command.SeriesSet.Symbols
            .Select(symbol => BuildObservation(symbol, asOf))
            .ToArray();
        return Task.FromResult<IReadOnlyList<MarketDataObservation>>(observations);
    }

    private static MarketDataObservation BuildObservation(string symbol, DateOnly asOf)
    {
        var meta = MarketDataSeriesCatalog.Resolve(symbol);
        var factor = DeterministicFactor(symbol, asOf);
        var value = meta.BaseValue + meta.Amplitude * (decimal)factor;
        return new MarketDataObservation(
            meta.ProviderSymbol,
            meta.Symbol,
            asOf,
            asOf,
            decimal.Round(value, 4, MidpointRounding.ToEven),
            meta.Unit);
    }

    private static double DeterministicFactor(string symbol, DateOnly asOf)
    {
        var seed = $"{symbol}|{asOf:yyyy-MM-dd}";
        var bytes = Encoding.UTF8.GetBytes(seed);
        var hash = SHA256.HashData(bytes);
        var shortHash = BitConverter.ToInt32(hash, 0);
        var normalized = (shortHash & 0x7FFFFFFF) / (double)0x7FFFFFFF;
        return (normalized * 2.0) - 1.0;
    }
}
