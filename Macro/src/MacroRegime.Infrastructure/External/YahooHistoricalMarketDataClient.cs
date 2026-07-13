using System.Globalization;
using System.Net;
using System.Text.Json;
using System.Text.Json.Serialization;
using MacroRegime.Application.External;

namespace MacroRegime.Infrastructure.External;

public sealed record YahooHistoricalMarketDataClientOptions
{
    public Uri BaseUri { get; init; } = new("https://query1.finance.yahoo.com");

    public int MaxAttempts { get; init; } = 3;

    public TimeSpan RetryDelay { get; init; } = TimeSpan.FromMilliseconds(500);
}

public sealed class YahooHistoricalMarketDataClient
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);
    private readonly HttpClient httpClient;
    private readonly YahooHistoricalMarketDataClientOptions options;

    public YahooHistoricalMarketDataClient(HttpClient httpClient, YahooHistoricalMarketDataClientOptions options)
    {
        this.httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
        this.options = options ?? throw new ArgumentNullException(nameof(options));
        if (options.MaxAttempts < 1)
        {
            throw new ArgumentException("Yahoo historical max attempts must be positive.", nameof(options));
        }
    }

    public async Task<IReadOnlyList<MarketDataObservation>> FetchHistoryAsync(
        DateOnly from,
        DateOnly to,
        IReadOnlyList<string> symbols,
        CancellationToken cancellationToken = default)
    {
        if (from > to)
        {
            throw new ArgumentException("Historical market from date must be on or before to date.", nameof(from));
        }

        ArgumentNullException.ThrowIfNull(symbols);
        var observations = new List<MarketDataObservation>();
        foreach (var symbol in symbols)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var metadata = MarketDataSeriesCatalog.Resolve(symbol);
            using var response = await SendWithRetryAsync(BuildUri(metadata.ProviderSymbol, from, to), cancellationToken).ConfigureAwait(false);
            await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
            var payload = await JsonSerializer.DeserializeAsync<YahooChartResponse>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false)
                ?? throw new InvalidDataException($"Yahoo returned an empty historical response for '{metadata.ProviderSymbol}'.");
            var result = payload.Chart?.Result?.FirstOrDefault()
                ?? throw new InvalidDataException($"Yahoo returned no historical result for '{metadata.ProviderSymbol}'.");
            var adjusted = result.Indicators?.AdjClose?.FirstOrDefault()?.AdjClose;
            var close = result.Indicators?.Quote?.FirstOrDefault()?.Close;
            for (var index = 0; index < result.Timestamp.Count; index++)
            {
                var observationDate = DateOnly.FromDateTime(DateTimeOffset.FromUnixTimeSeconds(result.Timestamp[index]).UtcDateTime);
                if (observationDate < from || observationDate > to)
                {
                    continue;
                }

                var value = ValueAt(adjusted, index) ?? ValueAt(close, index);
                if (value is null)
                {
                    continue;
                }

                observations.Add(new MarketDataObservation(
                    metadata.ProviderSymbol,
                    metadata.Symbol,
                    observationDate,
                    observationDate,
                    decimal.Round(value.Value, 6, MidpointRounding.ToEven),
                    metadata.Unit));
            }
        }

        return observations
            .OrderBy(item => item.ObservationDate)
            .ThenBy(item => item.Symbol, StringComparer.OrdinalIgnoreCase)
            .ToArray();
    }

    private Uri BuildUri(string providerSymbol, DateOnly from, DateOnly to)
    {
        var query = new Dictionary<string, string>
        {
            ["period1"] = ToUnixSeconds(from).ToString(CultureInfo.InvariantCulture),
            ["period2"] = ToUnixSeconds(to.AddDays(1)).ToString(CultureInfo.InvariantCulture),
            ["interval"] = "1d",
            ["events"] = "history",
            ["includeAdjustedClose"] = "true",
        };
        var builder = new UriBuilder(new Uri(options.BaseUri, $"/v8/finance/chart/{Uri.EscapeDataString(providerSymbol)}"))
        {
            Query = string.Join("&", query.Select(pair =>
                $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}")),
        };
        return builder.Uri;
    }

    private async Task<HttpResponseMessage> SendWithRetryAsync(Uri uri, CancellationToken cancellationToken)
    {
        for (var attempt = 1; ; attempt++)
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, uri);
            request.Headers.UserAgent.ParseAdd("MacroRegime/1.0");
            var response = await httpClient.SendAsync(request, cancellationToken).ConfigureAwait(false);
            if (response.IsSuccessStatusCode)
            {
                return response;
            }

            if (!ShouldRetry(response.StatusCode) || attempt >= options.MaxAttempts)
            {
                var content = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
                response.Dispose();
                throw new InvalidDataException($"Yahoo historical request failed with HTTP {(int)response.StatusCode} {response.ReasonPhrase}: {content}");
            }

            response.Dispose();
            await Task.Delay(options.RetryDelay, cancellationToken).ConfigureAwait(false);
        }
    }

    private static decimal? ValueAt(IReadOnlyList<decimal?>? values, int index) =>
        values is not null && index < values.Count ? values[index] : null;

    private static long ToUnixSeconds(DateOnly date) =>
        new DateTimeOffset(date.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero).ToUnixTimeSeconds();

    private static bool ShouldRetry(HttpStatusCode statusCode) => statusCode is
        HttpStatusCode.TooManyRequests or HttpStatusCode.InternalServerError or
        HttpStatusCode.BadGateway or HttpStatusCode.ServiceUnavailable or HttpStatusCode.GatewayTimeout;

    private sealed record YahooChartResponse([property: JsonPropertyName("chart")] YahooChart? Chart);
    private sealed record YahooChart([property: JsonPropertyName("result")] IReadOnlyList<YahooChartResult>? Result);
    private sealed record YahooChartResult(
        [property: JsonPropertyName("timestamp")] IReadOnlyList<long> Timestamp,
        [property: JsonPropertyName("indicators")] YahooIndicators? Indicators);
    private sealed record YahooIndicators(
        [property: JsonPropertyName("quote")] IReadOnlyList<YahooQuote>? Quote,
        [property: JsonPropertyName("adjclose")] IReadOnlyList<YahooAdjustedClose>? AdjClose);
    private sealed record YahooQuote([property: JsonPropertyName("close")] IReadOnlyList<decimal?>? Close);
    private sealed record YahooAdjustedClose([property: JsonPropertyName("adjclose")] IReadOnlyList<decimal?>? AdjClose);
}

