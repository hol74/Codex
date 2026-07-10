using System.Globalization;
using System.Net;
using System.Text.Json;
using System.Text.Json.Serialization;
using MacroRegime.Application.External;
using MacroRegime.Application.Ports;

namespace MacroRegime.Infrastructure.External;

public sealed record FredHttpMacroDataSourceOptions(string ApiKey)
{
    public Uri BaseUri { get; init; } = new("https://api.stlouisfed.org");

    public int MaxAttempts { get; init; } = 3;

    public TimeSpan RetryDelay { get; init; } = TimeSpan.FromMilliseconds(250);

    public int ObservationLimit { get; init; } = 30;

    public bool UseVintageDates { get; init; } = true;
}

public sealed class FredHttpMacroDataSource : IExternalMacroDataSource
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly HttpClient httpClient;
    private readonly FredHttpMacroDataSourceOptions options;

    public FredHttpMacroDataSource(HttpClient httpClient, FredHttpMacroDataSourceOptions options)
    {
        this.httpClient = httpClient;
        this.options = options;

        if (string.IsNullOrWhiteSpace(options.ApiKey))
        {
            throw new ArgumentException("FRED API key is required.", nameof(options));
        }

        if (options.MaxAttempts < 1)
        {
            throw new ArgumentException("Max attempts must be at least 1.", nameof(options));
        }

        if (options.ObservationLimit < 1)
        {
            throw new ArgumentException("Observation limit must be at least 1.", nameof(options));
        }
    }

    public async Task<IReadOnlyList<FredObservation>> FetchAsync(FredFetchCommand command, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        var observations = new List<FredObservation>(command.SeriesSet.SeriesCodes.Count);
        foreach (var seriesCode in command.SeriesSet.SeriesCodes)
        {
            cancellationToken.ThrowIfCancellationRequested();
            observations.Add(await FetchLatestObservationAsync(seriesCode, command.AsOfDate.Value, cancellationToken).ConfigureAwait(false));
        }

        return observations;
    }

    private async Task<FredObservation> FetchLatestObservationAsync(string seriesCode, DateOnly asOfDate, CancellationToken cancellationToken)
    {
        var metadata = FredSeriesCatalog.Resolve(seriesCode);
        try
        {
            var vintageDate = options.UseVintageDates
                ? await TryFetchLatestVintageDateAsync(metadata.FredSeriesId, asOfDate, cancellationToken).ConfigureAwait(false)
                : null;
            using var response = await SendWithRetryAsync(BuildObservationsUri(metadata, asOfDate, vintageDate), cancellationToken).ConfigureAwait(false);
            await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
            var payload = await JsonSerializer.DeserializeAsync<FredObservationsResponse>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false)
                ?? throw new InvalidDataException($"FRED returned an empty response for series '{metadata.FredSeriesId}'.");
            var observation = payload.Observations
                .Where(item => !string.IsNullOrWhiteSpace(item.Value) && item.Value != ".")
                .Select(item => TryMapObservation(item, metadata, asOfDate))
                .FirstOrDefault(item => item is not null);

            return observation
                ?? throw new InvalidDataException($"FRED returned no usable observations for series '{metadata.FredSeriesId}' on or before {asOfDate:yyyy-MM-dd}.");
        }
        catch (InvalidDataException exception)
        {
            throw new InvalidDataException($"FRED fetch failed for series '{metadata.SeriesCode}' ({metadata.FredSeriesId}): {exception.Message}", exception);
        }
    }

    private async Task<DateOnly?> TryFetchLatestVintageDateAsync(string seriesId, DateOnly asOfDate, CancellationToken cancellationToken)
    {
        using var response = await SendWithRetryOrNullForFredOnlySeriesAsync(BuildVintageDatesUri(seriesId, asOfDate), cancellationToken).ConfigureAwait(false);
        if (response is null)
        {
            return null;
        }

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        var payload = await JsonSerializer.DeserializeAsync<FredVintageDatesResponse>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false)
            ?? throw new InvalidDataException($"FRED returned an empty vintage-date response for series '{seriesId}'.");
        foreach (var item in payload.VintageDates)
        {
            if (DateOnly.TryParseExact(item, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var vintageDate))
            {
                return vintageDate;
            }
        }

        throw new InvalidDataException($"FRED returned no vintage dates for series '{seriesId}' on or before {asOfDate:yyyy-MM-dd}.");
    }

    private async Task<HttpResponseMessage?> SendWithRetryOrNullForFredOnlySeriesAsync(Uri uri, CancellationToken cancellationToken)
    {
        try
        {
            return await SendWithRetryAsync(uri, cancellationToken).ConfigureAwait(false);
        }
        catch (InvalidDataException exception) when (exception.Message.Contains("does not exist in ALFRED", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }
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
                throw new InvalidDataException($"FRED request failed with HTTP {(int)response.StatusCode} {response.ReasonPhrase}: {content}");
            }

            response.Dispose();
            if (options.RetryDelay > TimeSpan.Zero)
            {
                await Task.Delay(options.RetryDelay, cancellationToken).ConfigureAwait(false);
            }
        }
    }

    private Uri BuildObservationsUri(FredSeriesMetadata metadata, DateOnly asOfDate, DateOnly? vintageDate)
    {
        var query = new Dictionary<string, string>
        {
            ["series_id"] = metadata.FredSeriesId,
            ["api_key"] = options.ApiKey,
            ["file_type"] = "json",
            ["sort_order"] = "desc",
            ["limit"] = options.ObservationLimit.ToString(CultureInfo.InvariantCulture),
            ["observation_end"] = asOfDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
        };

        if (vintageDate is not null)
        {
            query["vintage_dates"] = vintageDate.Value.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        }

        if (!string.IsNullOrWhiteSpace(metadata.FredUnits))
        {
            query["units"] = metadata.FredUnits;
        }

        var builder = new UriBuilder(new Uri(options.BaseUri, "/fred/series/observations"))
        {
            Query = string.Join("&", query.Select(pair =>
                $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}")),
        };
        return builder.Uri;
    }

    private Uri BuildVintageDatesUri(string seriesId, DateOnly asOfDate)
    {
        var query = new Dictionary<string, string>
        {
            ["series_id"] = seriesId,
            ["api_key"] = options.ApiKey,
            ["file_type"] = "json",
            ["sort_order"] = "desc",
            ["limit"] = "1",
            ["realtime_end"] = asOfDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
        };

        var builder = new UriBuilder(new Uri(options.BaseUri, "/fred/series/vintagedates"))
        {
            Query = string.Join("&", query.Select(pair =>
                $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}")),
        };
        return builder.Uri;
    }

    private static FredObservation? TryMapObservation(FredObservationItem item, FredSeriesMetadata metadata, DateOnly asOfDate)
    {
        if (!DateOnly.TryParseExact(item.Date, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var observationDate))
        {
            return null;
        }

        if (!decimal.TryParse(item.Value, NumberStyles.Number, CultureInfo.InvariantCulture, out var value))
        {
            return null;
        }

        var publicationDate = ParseDateOrDefault(item.RealtimeStart, asOfDate);
        var vintageDate = ParseDateOrDefault(item.RealtimeEnd, asOfDate);
        return new FredObservation(
            metadata.FredSeriesId,
            metadata.SeriesCode,
            observationDate,
            publicationDate,
            vintageDate,
            value,
            metadata.Unit);
    }

    private static DateOnly ParseDateOrDefault(string? value, DateOnly fallback)
    {
        return DateOnly.TryParseExact(value, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var parsed)
            ? parsed
            : fallback;
    }

    private static bool ShouldRetry(HttpStatusCode statusCode)
    {
        return statusCode is HttpStatusCode.TooManyRequests
            or HttpStatusCode.InternalServerError
            or HttpStatusCode.BadGateway
            or HttpStatusCode.ServiceUnavailable
            or HttpStatusCode.GatewayTimeout;
    }

    private sealed record FredObservationsResponse(
        [property: JsonPropertyName("observations")] IReadOnlyList<FredObservationItem> Observations);

    private sealed record FredVintageDatesResponse(
        [property: JsonPropertyName("vintage_dates")] IReadOnlyList<string> VintageDates);

    private sealed record FredObservationItem(
        [property: JsonPropertyName("realtime_start")] string? RealtimeStart,
        [property: JsonPropertyName("realtime_end")] string? RealtimeEnd,
        [property: JsonPropertyName("date")] string Date,
        [property: JsonPropertyName("value")] string Value);
}
