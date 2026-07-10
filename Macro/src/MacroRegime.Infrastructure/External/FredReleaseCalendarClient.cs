using System.Globalization;
using System.Net;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace MacroRegime.Infrastructure.External;

public sealed record FredReleaseDate(int? ReleaseId, string? ReleaseName, DateOnly Date);

public sealed record FredReleaseCalendarOptions(string ApiKey)
{
    public Uri BaseUri { get; init; } = new("https://api.stlouisfed.org");

    public int MaxAttempts { get; init; } = 3;

    public TimeSpan RetryDelay { get; init; } = TimeSpan.FromMilliseconds(250);

    public int Limit { get; init; } = 1000;
}

public sealed class FredReleaseCalendarClient
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly HttpClient httpClient;
    private readonly FredReleaseCalendarOptions options;

    public FredReleaseCalendarClient(HttpClient httpClient, FredReleaseCalendarOptions options)
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

        if (options.Limit < 1)
        {
            throw new ArgumentException("Limit must be at least 1.", nameof(options));
        }
    }

    public async Task<IReadOnlyList<FredReleaseDate>> FetchAllReleaseDatesAsync(
        DateOnly realtimeStart,
        DateOnly realtimeEnd,
        bool includeReleaseDatesWithNoData = false,
        CancellationToken cancellationToken = default)
    {
        using var response = await SendWithRetryAsync(
                BuildAllReleaseDatesUri(realtimeStart, realtimeEnd, includeReleaseDatesWithNoData),
                cancellationToken)
            .ConfigureAwait(false);
        return await ReadReleaseDatesAsync(response, cancellationToken).ConfigureAwait(false);
    }

    public async Task<IReadOnlyList<FredReleaseDate>> FetchReleaseDatesAsync(
        int releaseId,
        DateOnly realtimeStart,
        DateOnly realtimeEnd,
        bool includeReleaseDatesWithNoData = false,
        CancellationToken cancellationToken = default)
    {
        using var response = await SendWithRetryAsync(
                BuildReleaseDatesUri(releaseId, realtimeStart, realtimeEnd, includeReleaseDatesWithNoData),
                cancellationToken)
            .ConfigureAwait(false);
        return await ReadReleaseDatesAsync(response, cancellationToken).ConfigureAwait(false);
    }

    private async Task<IReadOnlyList<FredReleaseDate>> ReadReleaseDatesAsync(HttpResponseMessage response, CancellationToken cancellationToken)
    {
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        var payload = await JsonSerializer.DeserializeAsync<FredReleaseDatesResponse>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false)
            ?? throw new InvalidDataException("FRED returned an empty release-date response.");
        return payload.ReleaseDates
            .Select(TryMapReleaseDate)
            .Where(item => item is not null)
            .Select(item => item!)
            .ToArray();
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
                throw new InvalidDataException($"FRED release calendar request failed with HTTP {(int)response.StatusCode} {response.ReasonPhrase}: {content}");
            }

            response.Dispose();
            if (options.RetryDelay > TimeSpan.Zero)
            {
                await Task.Delay(options.RetryDelay, cancellationToken).ConfigureAwait(false);
            }
        }
    }

    private Uri BuildAllReleaseDatesUri(DateOnly realtimeStart, DateOnly realtimeEnd, bool includeReleaseDatesWithNoData)
    {
        var query = BaseQuery(realtimeStart, realtimeEnd, includeReleaseDatesWithNoData);
        query["order_by"] = "release_date";
        query["sort_order"] = "asc";
        return BuildUri("/fred/releases/dates", query);
    }

    private Uri BuildReleaseDatesUri(int releaseId, DateOnly realtimeStart, DateOnly realtimeEnd, bool includeReleaseDatesWithNoData)
    {
        var query = BaseQuery(realtimeStart, realtimeEnd, includeReleaseDatesWithNoData);
        query["release_id"] = releaseId.ToString(CultureInfo.InvariantCulture);
        query["sort_order"] = "asc";
        return BuildUri("/fred/release/dates", query);
    }

    private Dictionary<string, string> BaseQuery(DateOnly realtimeStart, DateOnly realtimeEnd, bool includeReleaseDatesWithNoData)
    {
        return new Dictionary<string, string>
        {
            ["api_key"] = options.ApiKey,
            ["file_type"] = "json",
            ["realtime_start"] = realtimeStart.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["realtime_end"] = realtimeEnd.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["limit"] = options.Limit.ToString(CultureInfo.InvariantCulture),
            ["include_release_dates_with_no_data"] = includeReleaseDatesWithNoData ? "true" : "false",
        };
    }

    private Uri BuildUri(string path, IReadOnlyDictionary<string, string> query)
    {
        var builder = new UriBuilder(new Uri(options.BaseUri, path))
        {
            Query = string.Join("&", query.Select(pair =>
                $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}")),
        };
        return builder.Uri;
    }

    private static FredReleaseDate? TryMapReleaseDate(FredReleaseDateItem item)
    {
        if (!DateOnly.TryParseExact(item.Date, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var date))
        {
            return null;
        }

        return new FredReleaseDate(item.ReleaseId, item.ReleaseName, date);
    }

    private static bool ShouldRetry(HttpStatusCode statusCode)
    {
        return statusCode is HttpStatusCode.TooManyRequests
            or HttpStatusCode.InternalServerError
            or HttpStatusCode.BadGateway
            or HttpStatusCode.ServiceUnavailable
            or HttpStatusCode.GatewayTimeout;
    }

    private sealed record FredReleaseDatesResponse(
        [property: JsonPropertyName("release_dates")] IReadOnlyList<FredReleaseDateItem> ReleaseDates);

    private sealed record FredReleaseDateItem(
        [property: JsonPropertyName("release_id")] int? ReleaseId,
        [property: JsonPropertyName("release_name")] string? ReleaseName,
        [property: JsonPropertyName("date")] string Date);
}
