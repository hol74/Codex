using System.Globalization;
using System.Net;
using System.Text.Json;
using System.Text.Json.Serialization;
using MacroRegime.Application.External;

namespace MacroRegime.Infrastructure.External;

public sealed record FredHistoricalDataClientOptions(string ApiKey)
{
    public Uri BaseUri { get; init; } = new("https://api.stlouisfed.org");

    public int MaxAttempts { get; init; } = 3;

    public TimeSpan RetryDelay { get; init; } = TimeSpan.FromMilliseconds(500);

    public int ObservationLimit { get; init; } = 100_000;
}

public sealed class FredHistoricalDataClient
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);
    private readonly HttpClient httpClient;
    private readonly FredHistoricalDataClientOptions options;

    public FredHistoricalDataClient(HttpClient httpClient, FredHistoricalDataClientOptions options)
    {
        this.httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
        this.options = options ?? throw new ArgumentNullException(nameof(options));
        if (string.IsNullOrWhiteSpace(options.ApiKey))
        {
            throw new ArgumentException("FRED API key is required.", nameof(options));
        }

        if (options.MaxAttempts < 1 || options.ObservationLimit < 1)
        {
            throw new ArgumentException("FRED historical client options are invalid.", nameof(options));
        }
    }

    public async Task<IReadOnlyList<FredObservation>> FetchInitialReleaseHistoryAsync(
        DateOnly from,
        DateOnly to,
        IReadOnlyList<string> seriesCodes,
        CancellationToken cancellationToken = default)
    {
        if (from > to)
        {
            throw new ArgumentException("Historical FRED from date must be on or before to date.", nameof(from));
        }

        ArgumentNullException.ThrowIfNull(seriesCodes);
        var observations = new List<FredObservation>();
        foreach (var seriesCode in seriesCodes)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var metadata = FredSeriesCatalog.Resolve(seriesCode);
            var providerSeriesId = seriesCode.ToUpperInvariant() switch
            {
                "SAHM" => "UNRATE",
                // BAMLH0A0HYM2 was limited to three years of observations from April 2026.
                // BAA10Y preserves the long credit-spread history needed by the research corpus.
                "HY_OAS" => "BAA10Y",
                _ => metadata.FredSeriesId,
            };
            try
            {
                if (string.Equals(seriesCode, "SAHM", StringComparison.OrdinalIgnoreCase))
                {
                    var unemployment = await FetchSeriesAsync(metadata, "UNRATE", from, to, cancellationToken).ConfigureAwait(false);
                    var derived = TransformSahm(metadata, unemployment);
                    var official = await FetchSeriesAsync(metadata, metadata.FredSeriesId, from, to, cancellationToken).ConfigureAwait(false);
                    observations.AddRange(MergeSahmHistory(derived, official));
                    continue;
                }

                var raw = string.Equals(metadata.Frequency, "daily", StringComparison.OrdinalIgnoreCase)
                    ? await FetchCurrentSeriesAsync(metadata, providerSeriesId, from, to, cancellationToken).ConfigureAwait(false)
                    : await FetchSeriesAsync(metadata, providerSeriesId, from, to, cancellationToken).ConfigureAwait(false);
                observations.AddRange(Transform(metadata, raw));
            }
            catch (InvalidDataException exception)
            {
                throw new InvalidDataException(
                    $"FRED historical fetch failed for '{seriesCode}' ({providerSeriesId}): {exception.Message}", exception);
            }
        }

        return observations
            .OrderBy(item => item.SeriesCode, StringComparer.OrdinalIgnoreCase)
            .ThenBy(item => item.ObservationDate)
            .ToArray();
    }

    private async Task<IReadOnlyList<FredObservation>> FetchCurrentSeriesAsync(
        FredSeriesMetadata metadata,
        string providerSeriesId,
        DateOnly from,
        DateOnly to,
        CancellationToken cancellationToken)
    {
        var query = new Dictionary<string, string>
        {
            ["series_id"] = providerSeriesId,
            ["api_key"] = options.ApiKey,
            ["file_type"] = "json",
            ["sort_order"] = "asc",
            ["limit"] = options.ObservationLimit.ToString(CultureInfo.InvariantCulture),
            ["observation_start"] = from.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["observation_end"] = to.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
        };
        using var response = await SendWithRetryAsync(
            BuildUri(options.BaseUri, "/fred/series/observations", query), cancellationToken).ConfigureAwait(false);
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        var payload = await JsonSerializer.DeserializeAsync<FredHistoryResponse>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false)
            ?? throw new InvalidDataException($"FRED returned an empty current-history response for '{providerSeriesId}'.");
        if (payload.Count > payload.Observations.Count)
        {
            throw new InvalidDataException($"FRED current-history response for '{providerSeriesId}' was truncated.");
        }

        return payload.Observations
            .Select(item =>
            {
                if (!DateOnly.TryParseExact(item.Date, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var observationDate)
                    || !decimal.TryParse(item.Value, NumberStyles.Number, CultureInfo.InvariantCulture, out var value))
                {
                    return null;
                }

                return new FredObservation(
                    providerSeriesId,
                    metadata.SeriesCode,
                    observationDate,
                    observationDate,
                    observationDate,
                    value,
                    metadata.Unit);
            })
            .Where(item => item is not null)
            .Select(item => item!)
            .ToArray();
    }

    private async Task<IReadOnlyList<FredObservation>> FetchSeriesAsync(
        FredSeriesMetadata metadata,
        string providerSeriesId,
        DateOnly from,
        DateOnly to,
        CancellationToken cancellationToken)
    {
        var historyStart = from.AddYears(-2);
        var mapped = new List<FredObservation>();
        for (var chunkStart = historyStart; chunkStart <= to; chunkStart = chunkStart.AddYears(5))
        {
            var chunkEndCandidate = chunkStart.AddYears(5).AddDays(-1);
            var chunkEnd = chunkEndCandidate < to ? chunkEndCandidate : to;
            using var response = await SendWithRetryAsync(
                BuildUri(providerSeriesId, historyStart, to, chunkStart, chunkEnd), cancellationToken).ConfigureAwait(false);
            await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
            var payload = await JsonSerializer.DeserializeAsync<FredHistoryResponse>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false)
                ?? throw new InvalidDataException($"FRED returned an empty historical response for '{metadata.FredSeriesId}'.");
            if (payload.Count > payload.Observations.Count)
            {
                throw new InvalidDataException($"FRED historical response for '{metadata.FredSeriesId}' was truncated at {payload.Observations.Count} of {payload.Count} observations.");
            }

            foreach (var item in payload.Observations)
            {
                if (!DateOnly.TryParseExact(item.Date, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var observationDate)
                    || !DateOnly.TryParseExact(item.RealtimeStart, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var publicationDate)
                    || !decimal.TryParse(item.Value, NumberStyles.Number, CultureInfo.InvariantCulture, out var value))
                {
                    continue;
                }

                mapped.Add(new FredObservation(
                    providerSeriesId,
                    metadata.SeriesCode,
                    observationDate,
                    publicationDate,
                    publicationDate,
                    value,
                    metadata.FredUnits is null ? metadata.Unit : "Index"));
            }
        }

        return mapped
            .GroupBy(item => (item.ObservationDate, item.PublicationDate))
            .Select(group => group.First())
            .OrderBy(item => item.ObservationDate)
            .ToArray();
    }

    private static IReadOnlyList<FredObservation> Transform(
        FredSeriesMetadata metadata,
        IReadOnlyList<FredObservation> raw)
    {
        if (!string.Equals(metadata.FredUnits, "pc1", StringComparison.OrdinalIgnoreCase))
        {
            return string.Equals(metadata.SeriesCode, "SAHM", StringComparison.OrdinalIgnoreCase)
                ? TransformSahm(metadata, raw)
                : raw;
        }

        var byDate = raw
            .GroupBy(item => item.ObservationDate)
            .ToDictionary(group => group.Key, group => group.OrderBy(item => item.PublicationDate).First());
        var transformed = new List<FredObservation>();
        foreach (var current in byDate.Values.OrderBy(item => item.ObservationDate))
        {
            if (!byDate.TryGetValue(current.ObservationDate.AddYears(-1), out var previous) || previous.Value == 0m)
            {
                continue;
            }

            transformed.Add(current with
            {
                Value = decimal.Round(((current.Value / previous.Value) - 1m) * 100m, 6, MidpointRounding.ToEven),
                Unit = metadata.Unit,
            });
        }

        return transformed;
    }

    private static IReadOnlyList<FredObservation> TransformSahm(
        FredSeriesMetadata metadata,
        IReadOnlyList<FredObservation> unemployment)
    {
        var byDate = unemployment
            .GroupBy(item => item.ObservationDate)
            .ToDictionary(group => group.Key, group => group.OrderBy(item => item.PublicationDate).First());
        var movingAverages = new SortedDictionary<DateOnly, decimal>();
        foreach (var current in byDate.Values.OrderBy(item => item.ObservationDate))
        {
            if (!byDate.TryGetValue(current.ObservationDate.AddMonths(-1), out var previous1)
                || !byDate.TryGetValue(current.ObservationDate.AddMonths(-2), out var previous2))
            {
                continue;
            }

            movingAverages[current.ObservationDate] = (current.Value + previous1.Value + previous2.Value) / 3m;
        }

        var transformed = new List<FredObservation>();
        foreach (var (observationDate, currentAverage) in movingAverages)
        {
            var priorAverages = movingAverages
                .Where(pair => pair.Key >= observationDate.AddMonths(-12) && pair.Key < observationDate)
                .Select(pair => pair.Value)
                .ToArray();
            if (priorAverages.Length < 12 || !byDate.TryGetValue(observationDate, out var current))
            {
                continue;
            }

            transformed.Add(new FredObservation(
                "UNRATE",
                metadata.SeriesCode,
                observationDate,
                current.PublicationDate,
                current.PublicationDate,
                decimal.Round(currentAverage - priorAverages.Min(), 6, MidpointRounding.ToEven),
                metadata.Unit));
        }

        return transformed;
    }

    private static IReadOnlyList<FredObservation> MergeSahmHistory(
        IReadOnlyList<FredObservation> derived,
        IReadOnlyList<FredObservation> official)
    {
        // Keep the UNRATE-derived series used by the development corpus wherever it is
        // computable. Official real-time SAHM initial releases fill dates that cannot be
        // reconstructed because the unemployment release history contains a gap.
        var byDate = official
            .GroupBy(item => item.ObservationDate)
            .ToDictionary(group => group.Key, group => group.OrderBy(item => item.PublicationDate).First());
        foreach (var observation in derived)
        {
            byDate[observation.ObservationDate] = observation;
        }

        return byDate.Values
            .OrderBy(item => item.ObservationDate)
            .ToArray();
    }

    private Uri BuildUri(
        string seriesId,
        DateOnly observationStart,
        DateOnly observationEnd,
        DateOnly realtimeStart,
        DateOnly realtimeEnd)
    {
        var query = new Dictionary<string, string>
        {
            ["series_id"] = seriesId,
            ["api_key"] = options.ApiKey,
            ["file_type"] = "json",
            ["output_type"] = "4",
            ["sort_order"] = "asc",
            ["limit"] = options.ObservationLimit.ToString(CultureInfo.InvariantCulture),
            ["realtime_start"] = realtimeStart.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["realtime_end"] = realtimeEnd.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["observation_start"] = observationStart.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["observation_end"] = observationEnd.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
        };
        return BuildUri(options.BaseUri, "/fred/series/observations", query);
    }

    private async Task<HttpResponseMessage> SendWithRetryAsync(Uri uri, CancellationToken cancellationToken)
    {
        for (var attempt = 1; ; attempt++)
        {
            var response = await httpClient.GetAsync(uri, cancellationToken).ConfigureAwait(false);
            if (response.IsSuccessStatusCode)
            {
                return response;
            }

            if (!ShouldRetry(response.StatusCode) || attempt >= options.MaxAttempts)
            {
                var content = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
                response.Dispose();
                throw new InvalidDataException($"FRED historical request failed with HTTP {(int)response.StatusCode} {response.ReasonPhrase}: {content}");
            }

            response.Dispose();
            await Task.Delay(options.RetryDelay, cancellationToken).ConfigureAwait(false);
        }
    }

    private static Uri BuildUri(Uri baseUri, string path, IReadOnlyDictionary<string, string> query)
    {
        var builder = new UriBuilder(new Uri(baseUri, path))
        {
            Query = string.Join("&", query.Select(pair =>
                $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}")),
        };
        return builder.Uri;
    }

    private static bool ShouldRetry(HttpStatusCode statusCode) => statusCode is
        HttpStatusCode.TooManyRequests or HttpStatusCode.InternalServerError or
        HttpStatusCode.BadGateway or HttpStatusCode.ServiceUnavailable or HttpStatusCode.GatewayTimeout;

    private sealed record FredHistoryResponse(
        [property: JsonPropertyName("count")] int Count,
        [property: JsonPropertyName("observations")] IReadOnlyList<FredHistoryItem> Observations);

    private sealed record FredHistoryItem(
        [property: JsonPropertyName("realtime_start")] string RealtimeStart,
        [property: JsonPropertyName("date")] string Date,
        [property: JsonPropertyName("value")] string Value);
}
