using System.Security.Cryptography;
using System.Text;
using MacroRegime.Application.External;
using MacroRegime.Application.Ports;

namespace MacroRegime.Infrastructure.External;

public sealed class FredStubMacroDataSource : IExternalMacroDataSource
{
    public Task<IReadOnlyList<FredObservation>> FetchAsync(FredFetchCommand command, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        var asOf = command.AsOfDate.Value;
        var observations = command.SeriesSet.SeriesCodes
            .Select(code => BuildObservation(code, asOf))
            .ToArray();
        return Task.FromResult<IReadOnlyList<FredObservation>>(observations);
    }

    private static FredObservation BuildObservation(string seriesCode, DateOnly asOf)
    {
        var meta = FredSeriesCatalog.Resolve(seriesCode);
        var factor = DeterministicFactor(seriesCode, asOf);
        var value = meta.BaseValue + meta.Amplitude * (decimal)factor;
        var observationDate = meta.Frequency == "daily"
            ? asOf
            : LastDayOfPreviousMonth(asOf);
        return new FredObservation(
            meta.FredSeriesId,
            meta.SeriesCode,
            observationDate,
            asOf,
            asOf,
            decimal.Round(value, 4, MidpointRounding.ToEven),
            meta.Unit);
    }

    private static double DeterministicFactor(string seriesCode, DateOnly asOf)
    {
        var seed = $"{seriesCode}|{asOf:yyyy-MM-dd}";
        var bytes = Encoding.UTF8.GetBytes(seed);
        var hash = SHA256.HashData(bytes);
        var shortHash = BitConverter.ToInt32(hash, 0);
        var normalized = (shortHash & 0x7FFFFFFF) / (double)0x7FFFFFFF;
        return (normalized * 2.0) - 1.0;
    }

    private static DateOnly LastDayOfPreviousMonth(DateOnly asOf)
    {
        var firstOfThisMonth = new DateOnly(asOf.Year, asOf.Month, 1);
        return firstOfThisMonth.AddDays(-1);
    }
}
