using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using MacroRegime.Application.External;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.External;

public sealed record PopulateHistoricalDataCommand(
    DateOnly From,
    DateOnly To,
    string MacroDataDirectory,
    string MarketDataDirectory,
    string ManifestPath,
    int MaxForwardHorizonDays = 91);

public sealed record PopulateHistoricalDataResult(
    DateOnly FirstSampleDate,
    DateOnly LastSampleDate,
    int MacroSnapshotCount,
    int MarketSnapshotCount,
    string ManifestPath);

public sealed record HistoricalDataCorpusManifest(
    int SchemaVersion,
    DateOnly RequestedFrom,
    DateOnly RequestedTo,
    DateOnly FirstSampleDate,
    DateOnly LastSampleDate,
    string Sampling,
    string MacroSource,
    string MacroVintagePolicy,
    string MarketSource,
    string MarketPricePolicy,
    IReadOnlyList<string> MacroSeries,
    IReadOnlyList<string> MarketSymbols,
    IReadOnlyDictionary<string, int> IntramonthFeatureObservationCounts,
    int MacroSnapshotCount,
    int MarketSnapshotCount,
    long TotalBytes,
    string AggregateSha256);

public sealed class HistoricalDataPopulator
{
    private const int ManifestSchemaVersion = 2;
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web) { WriteIndented = true };
    private readonly FredHistoricalDataClient fredClient;
    private readonly YahooHistoricalMarketDataClient marketClient;
    private readonly JsonMacroDataFileWriter macroWriter = new();
    private readonly JsonMarketDataFileWriter marketWriter = new();

    public HistoricalDataPopulator(
        FredHistoricalDataClient fredClient,
        YahooHistoricalMarketDataClient marketClient)
    {
        this.fredClient = fredClient ?? throw new ArgumentNullException(nameof(fredClient));
        this.marketClient = marketClient ?? throw new ArgumentNullException(nameof(marketClient));
    }

    public async Task<PopulateHistoricalDataResult> PopulateAsync(
        PopulateHistoricalDataCommand command,
        CancellationToken cancellationToken = default)
    {
        Validate(command);
        var marketTo = command.To.AddDays(command.MaxForwardHorizonDays + 10);
        var macroHistory = await fredClient.FetchInitialReleaseHistoryAsync(
            command.From.AddMonths(-3), command.To, FredSeriesCatalog.HistoricalSourceSeriesCodes, cancellationToken).ConfigureAwait(false);
        var marketHistory = await marketClient.FetchHistoryAsync(
            command.From.AddDays(-10), marketTo, MarketDataSeriesCatalog.BaselineSymbols, cancellationToken).ConfigureAwait(false);

        var completeMarketDates = marketHistory
            .GroupBy(item => item.ObservationDate)
            .Where(group => group.Select(item => item.Symbol).Distinct(StringComparer.OrdinalIgnoreCase).Count()
                == MarketDataSeriesCatalog.BaselineSymbols.Count)
            .ToDictionary(group => group.Key, group => (IReadOnlyList<MarketDataObservation>)group.ToArray());
        var sampleDates = completeMarketDates.Keys
            .Where(date => date >= command.From && date <= command.To)
            .GroupBy(date => (date.Year, date.Month))
            .Select(group => group.Max())
            .OrderBy(date => date)
            .ToArray();
        if (sampleDates.Length == 0)
        {
            throw new InvalidDataException("No complete monthly market sample dates were found.");
        }

        Directory.CreateDirectory(command.MacroDataDirectory);
        Directory.CreateDirectory(command.MarketDataDirectory);
        var marketPaths = new List<string>();
        var writtenMarketDates = completeMarketDates.Keys
            .Where(date => date >= command.From && date <= marketTo)
            .OrderBy(date => date)
            .ToArray();
        foreach (var date in writtenMarketDates)
        {
            cancellationToken.ThrowIfCancellationRequested();
            marketPaths.Add(await marketWriter.WriteAsync(completeMarketDates[date], new AsOfDate(date), command.MarketDataDirectory, cancellationToken).ConfigureAwait(false));
        }

        var macroBySeries = macroHistory
            .GroupBy(item => item.SeriesCode, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(group => group.Key, group => group.OrderBy(item => item.ObservationDate).ToArray(), StringComparer.OrdinalIgnoreCase);
        var macroPaths = new List<string>();
        var intramonthFeatureObservationCounts = FredSeriesCatalog.HistoricalIntramonthDerivedSeriesCodes
            .ToDictionary(code => code, _ => 0, StringComparer.OrdinalIgnoreCase);
        foreach (var date in sampleDates)
        {
            var snapshot = FredSeriesCatalog.BaselineSeriesCodes.Select(code =>
            {
                if (!macroBySeries.TryGetValue(code, out var series))
                {
                    throw new InvalidDataException($"No FRED initial-release history was returned for '{code}'.");
                }

                var observation = series.LastOrDefault(item => item.ObservationDate <= date && item.PublicationDate <= date)
                    ?? throw new InvalidDataException($"No point-in-time FRED observation for '{code}' as of {date:yyyy-MM-dd}.");
                ValidateMonthlyFreshness(code, date, observation);
                return observation;
            }).ToList();
            snapshot.Add(DeriveThreeMonthChange(date, macroBySeries, "CPI_YOY", "CPI_YOY_3M_CHANGE"));
            snapshot.Add(DeriveThreeMonthChange(date, macroBySeries, "YC_10Y2Y", "YC_10Y2Y_3M_CHANGE"));
            AddIfAvailable(snapshot, DeriveMonthlyMaximum(date, macroBySeries, "VIX", "VIX_MONTHLY_MAX"), intramonthFeatureObservationCounts);
            AddIfAvailable(snapshot, DeriveMonthlyFundingSpreadMaximum(date, macroBySeries), intramonthFeatureObservationCounts);
            AddIfAvailable(snapshot, DeriveMonthlyMarketDrawdown(date, marketHistory, "SPY", "SPY_MONTHLY_MAX_DRAWDOWN"), intramonthFeatureObservationCounts);
            AddIfAvailable(snapshot, DeriveMonthlyMarketDrawdown(date, marketHistory, "HYG", "HYG_MONTHLY_MAX_DRAWDOWN"), intramonthFeatureObservationCounts);
            macroPaths.Add(await macroWriter.WriteAsync(snapshot, new AsOfDate(date), command.MacroDataDirectory, cancellationToken).ConfigureAwait(false));
        }

        var files = macroPaths
            .Concat(marketPaths)
            .OrderBy(path => path, StringComparer.OrdinalIgnoreCase)
            .ToArray();
        var (totalBytes, aggregateHash) = await HashCorpusAsync(files, cancellationToken).ConfigureAwait(false);
        var manifest = new HistoricalDataCorpusManifest(
            ManifestSchemaVersion,
            command.From,
            command.To,
            sampleDates[0],
            sampleDates[^1],
            "last-complete-trading-day-of-month",
            "FRED/ALFRED",
            "monthly revisionable series use ALFRED initial releases; INDPRO and CPI YoY are computed from initial-release levels; SAHM uses UNRATE-derived initial releases where computable and official SAHMREALTIME initial releases to fill release-history gaps; three-month changes use only observations available at each cutoff; VIX maximum, SOFR-EFFR maximum spread and SPY/HYG maximum drawdowns aggregate only observations from the current calendar month available by the sample date; daily financial series use current history and are not vintage; missing SOFR-era features remain absent and are counted explicitly; HY_OAS uses the long-history FRED BAA10Y proxy",
            "Yahoo Finance chart endpoint",
            "adjusted-close with close fallback",
            FredSeriesCatalog.HistoricalSnapshotSeriesCodes,
            MarketDataSeriesCatalog.BaselineSymbols,
            intramonthFeatureObservationCounts,
            sampleDates.Length,
            writtenMarketDates.Length,
            totalBytes,
            aggregateHash);
        var manifestPath = Path.GetFullPath(command.ManifestPath);
        Directory.CreateDirectory(Path.GetDirectoryName(manifestPath)!);
        await File.WriteAllTextAsync(manifestPath, JsonSerializer.Serialize(manifest, SerializerOptions), cancellationToken).ConfigureAwait(false);
        return new PopulateHistoricalDataResult(sampleDates[0], sampleDates[^1], sampleDates.Length, writtenMarketDates.Length, manifestPath);
    }

    private static void AddIfAvailable(
        ICollection<FredObservation> snapshot,
        FredObservation? observation,
        IDictionary<string, int> coverage)
    {
        if (observation is null)
        {
            return;
        }

        snapshot.Add(observation);
        coverage[observation.SeriesCode]++;
    }

    private static FredObservation? DeriveMonthlyMaximum(
        DateOnly sampleDate,
        IReadOnlyDictionary<string, FredObservation[]> macroBySeries,
        string sourceCode,
        string derivedCode)
    {
        if (!macroBySeries.TryGetValue(sourceCode, out var series))
        {
            return null;
        }

        var window = series.Where(item =>
                item.ObservationDate.Year == sampleDate.Year
                && item.ObservationDate.Month == sampleDate.Month
                && item.ObservationDate <= sampleDate
                && item.PublicationDate <= sampleDate)
            .ToArray();
        if (window.Length == 0)
        {
            return null;
        }

        var maximum = window.OrderByDescending(item => item.Value).ThenBy(item => item.ObservationDate).First();
        var metadata = FredSeriesCatalog.Resolve(derivedCode);
        return new FredObservation(metadata.FredSeriesId, derivedCode, maximum.ObservationDate, sampleDate, sampleDate, maximum.Value, metadata.Unit);
    }

    private static FredObservation? DeriveMonthlyFundingSpreadMaximum(
        DateOnly sampleDate,
        IReadOnlyDictionary<string, FredObservation[]> macroBySeries)
    {
        if (!macroBySeries.TryGetValue("SOFR", out var sofr) || !macroBySeries.TryGetValue("EFFR", out var effr))
        {
            return null;
        }

        var effrByDate = effr.Where(item => item.ObservationDate <= sampleDate && item.PublicationDate <= sampleDate)
            .GroupBy(item => item.ObservationDate)
            .ToDictionary(group => group.Key, group => group.Last());
        var spreads = sofr.Where(item =>
                item.ObservationDate.Year == sampleDate.Year
                && item.ObservationDate.Month == sampleDate.Month
                && item.ObservationDate <= sampleDate
                && item.PublicationDate <= sampleDate
                && effrByDate.ContainsKey(item.ObservationDate))
            .Select(item => (item.ObservationDate, Value: (item.Value - effrByDate[item.ObservationDate].Value) * 100m))
            .ToArray();
        if (spreads.Length == 0)
        {
            return null;
        }

        var maximum = spreads.OrderByDescending(item => item.Value).ThenBy(item => item.ObservationDate).First();
        var metadata = FredSeriesCatalog.Resolve("SOFR_EFFR_MONTHLY_MAX");
        return new FredObservation(metadata.FredSeriesId, metadata.SeriesCode, maximum.ObservationDate, sampleDate, sampleDate,
            decimal.Round(maximum.Value, 6, MidpointRounding.ToEven), metadata.Unit);
    }

    private static FredObservation? DeriveMonthlyMarketDrawdown(
        DateOnly sampleDate,
        IReadOnlyList<MarketDataObservation> marketHistory,
        string symbol,
        string derivedCode)
    {
        var window = marketHistory.Where(item =>
                string.Equals(item.Symbol, symbol, StringComparison.OrdinalIgnoreCase)
                && item.ObservationDate.Year == sampleDate.Year
                && item.ObservationDate.Month == sampleDate.Month
                && item.ObservationDate <= sampleDate
                && item.AvailabilityDate <= sampleDate)
            .OrderBy(item => item.ObservationDate)
            .ToArray();
        if (window.Length == 0)
        {
            return null;
        }

        var peak = window[0].Value;
        var maximumDrawdown = 0m;
        var maximumDate = window[0].ObservationDate;
        foreach (var observation in window)
        {
            peak = Math.Max(peak, observation.Value);
            if (peak == 0m)
            {
                continue;
            }

            var drawdown = ((peak - observation.Value) / peak) * 100m;
            if (drawdown > maximumDrawdown)
            {
                maximumDrawdown = drawdown;
                maximumDate = observation.ObservationDate;
            }
        }

        var metadata = FredSeriesCatalog.Resolve(derivedCode);
        return new FredObservation(metadata.FredSeriesId, metadata.SeriesCode, maximumDate, sampleDate, sampleDate,
            decimal.Round(maximumDrawdown, 6, MidpointRounding.ToEven), metadata.Unit);
    }

    private static FredObservation DeriveThreeMonthChange(
        DateOnly sampleDate,
        IReadOnlyDictionary<string, FredObservation[]> macroBySeries,
        string sourceCode,
        string derivedCode)
    {
        if (!macroBySeries.TryGetValue(sourceCode, out var series))
        {
            throw new InvalidDataException($"No FRED history was returned for derived source '{sourceCode}'.");
        }

        var current = series.LastOrDefault(item =>
            item.ObservationDate <= sampleDate && item.PublicationDate <= sampleDate)
            ?? throw new InvalidDataException($"No point-in-time '{sourceCode}' observation as of {sampleDate:yyyy-MM-dd}.");
        var priorCutoff = sampleDate.AddMonths(-3);
        var prior = series.LastOrDefault(item =>
            item.ObservationDate <= priorCutoff && item.PublicationDate <= priorCutoff)
            ?? throw new InvalidDataException($"No point-in-time '{sourceCode}' observation as of prior cutoff {priorCutoff:yyyy-MM-dd}.");
        var metadata = FredSeriesCatalog.Resolve(derivedCode);

        return new FredObservation(
            metadata.FredSeriesId,
            metadata.SeriesCode,
            current.ObservationDate,
            current.PublicationDate > prior.PublicationDate ? current.PublicationDate : prior.PublicationDate,
            current.VintageDate > prior.VintageDate ? current.VintageDate : prior.VintageDate,
            decimal.Round(current.Value - prior.Value, 6, MidpointRounding.ToEven),
            metadata.Unit);
    }

    private static void ValidateMonthlyFreshness(
        string seriesCode,
        DateOnly asOfDate,
        FredObservation observation)
    {
        var metadata = FredSeriesCatalog.Resolve(seriesCode);
        if (!string.Equals(metadata.Frequency, "monthly", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        var lagMonths = ((asOfDate.Year - observation.ObservationDate.Year) * 12)
            + asOfDate.Month - observation.ObservationDate.Month;
        if (lagMonths > 3)
        {
            throw new InvalidDataException(
                $"Stale monthly FRED observation for '{seriesCode}' as of {asOfDate:yyyy-MM-dd}: "
                + $"latest observation is {observation.ObservationDate:yyyy-MM-dd} ({lagMonths} months old; maximum 3).");
        }
    }

    private static void Validate(PopulateHistoricalDataCommand command)
    {
        ArgumentNullException.ThrowIfNull(command);
        if (command.From > command.To || command.MaxForwardHorizonDays <= 0)
        {
            throw new ArgumentException("Historical population date range or forward horizon is invalid.", nameof(command));
        }

        if (string.IsNullOrWhiteSpace(command.MacroDataDirectory)
            || string.IsNullOrWhiteSpace(command.MarketDataDirectory)
            || string.IsNullOrWhiteSpace(command.ManifestPath))
        {
            throw new ArgumentException("Historical population output paths are required.", nameof(command));
        }
    }

    private static async Task<(long TotalBytes, string AggregateHash)> HashCorpusAsync(
        IReadOnlyList<string> files,
        CancellationToken cancellationToken)
    {
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        long totalBytes = 0;
        foreach (var path in files)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var nameBytes = Encoding.UTF8.GetBytes(Path.GetFileName(path) + "\n");
            hash.AppendData(nameBytes);
            var bytes = await File.ReadAllBytesAsync(path, cancellationToken).ConfigureAwait(false);
            totalBytes += bytes.LongLength;
            hash.AppendData(bytes);
        }

        return (totalBytes, Convert.ToHexString(hash.GetHashAndReset()).ToLowerInvariant());
    }
}
