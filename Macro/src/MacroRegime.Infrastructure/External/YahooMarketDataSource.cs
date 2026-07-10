using System.Globalization;
using System.Net;
using System.Text.Json;
using System.Text.Json.Serialization;
using MacroRegime.Application.External;
using MacroRegime.Application.Ports;

namespace MacroRegime.Infrastructure.External;

public sealed record YahooMarketDataSourceOptions
{
    public Uri BaseUri { get; init; } = new("https://query1.finance.yahoo.com");

    public int MaxAttempts { get; init; } = 3;

    public TimeSpan RetryDelay { get; init; } = TimeSpan.FromMilliseconds(250);

    public int LookbackDays { get; init; } = 10;
}

public sealed class YahooMarketDataSource : IExternalMarketDataSource
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly HttpClient httpClient;
    private readonly YahooMarketDataSourceOptions options;

    public YahooMarketDataSource(HttpClient httpClient, YahooMarketDataSourceOptions options)
    {
        this.httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
        this.options = options ?? throw new ArgumentNullException(nameof(options));

        if (options.MaxAttempts < 1)
        {
            throw new ArgumentException("Max attempts must be at least 1.", nameof(options));
        }

        if (options.LookbackDays < 1)
        {
            throw new ArgumentException("Lookback days must be at least 1.", nameof(options));
        }
    }

    public async Task<IReadOnlyList<MarketDataObservation>> FetchAsync(MarketDataFetchCommand command, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        var observations = new List<MarketDataObservation>(command.SeriesSet.Symbols.Count);
        foreach (var symbol in command.SeriesSet.Symbols)
        {
            cancellationToken.ThrowIfCancellationRequested();
            observations.Add(await FetchLatestObservationAsync(symbol, command.AsOfDate.Value, cancellationToken).ConfigureAwait(false));
        }

        return observations;
    }

    private async Task<MarketDataObservation> FetchLatestObservationAsync(string symbol, DateOnly asOfDate, CancellationToken cancellationToken)
    {
        var metadata = MarketDataSeriesCatalog.Resolve(symbol);
        try
        {
            using var response = await SendWithRetryAsync(BuildChartUri(metadata.ProviderSymbol, asOfDate), cancellationToken).ConfigureAwait(false);
            await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
            var payload = await JsonSerializer.DeserializeAsync<YahooChartResponse>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false)
                ?? throw new InvalidDataException($"Yahoo returned an empty response for symbol '{metadata.ProviderSymbol}'.");

            var result = payload.Chart?.Result?.FirstOrDefault()
                ?? throw new InvalidDataException($"Yahoo returned no chart result for symbol '{metadata.ProviderSymbol}'.");

            if (result.Timestamp.Count == 0)
            {
                throw new InvalidDataException($"Yahoo returned no timestamps for symbol '{metadata.ProviderSymbol}'.");
            }

            var adjustedClose = result.Indicators?.AdjClose?.FirstOrDefault()?.AdjClose;
            var close = result.Indicators?.Quote?.FirstOrDefault()?.Close;
            var observation = SelectLatestUsableObservation(result.Timestamp, adjustedClose, close, asOfDate, metadata);

            return observation
                ?? throw new InvalidDataException($"Yahoo returned no usable close for symbol '{metadata.ProviderSymbol}' on or before {asOfDate:yyyy-MM-dd}.");
        }
        catch (InvalidDataException exception)
        {
            throw new InvalidDataException($"Yahoo market data fetch failed for symbol '{metadata.Symbol}' ({metadata.ProviderSymbol}): {exception.Message}", exception);
        }
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
                throw new InvalidDataException($"Yahoo chart request failed with HTTP {(int)response.StatusCode} {response.ReasonPhrase}: {content}");
            }

            response.Dispose();
            if (options.RetryDelay > TimeSpan.Zero)
            {
                await Task.Delay(options.RetryDelay, cancellationToken).ConfigureAwait(false);
            }
        }
    }

    private Uri BuildChartUri(string providerSymbol, DateOnly asOfDate)
    {
        var period1 = ToUnixSeconds(asOfDate.AddDays(-options.LookbackDays));
        var period2 = ToUnixSeconds(asOfDate.AddDays(1));
        var query = new Dictionary<string, string>
        {
            ["period1"] = period1.ToString(CultureInfo.InvariantCulture),
            ["period2"] = period2.ToString(CultureInfo.InvariantCulture),
            ["interval"] = "1d",
            ["events"] = "history",
            ["includeAdjustedClose"] = "true",
        };

        var escapedSymbol = Uri.EscapeDataString(providerSymbol);
        var builder = new UriBuilder(new Uri(options.BaseUri, $"/v8/finance/chart/{escapedSymbol}"))
        {
            Query = string.Join("&", query.Select(pair =>
                $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}")),
        };
        return builder.Uri;
    }

    private static MarketDataObservation? SelectLatestUsableObservation(
        IReadOnlyList<long> timestamps,
        IReadOnlyList<decimal?>? adjustedClose,
        IReadOnlyList<decimal?>? close,
        DateOnly asOfDate,
        MarketDataSeriesMetadata metadata)
    {
        for (var index = timestamps.Count - 1; index >= 0; index--)
        {
            var observationDate = DateOnly.FromDateTime(DateTimeOffset.FromUnixTimeSeconds(timestamps[index]).UtcDateTime);
            if (observationDate > asOfDate)
            {
                continue;
            }

            var value = ValueAt(adjustedClose, index) ?? ValueAt(close, index);
            if (value is null)
            {
                continue;
            }

            return new MarketDataObservation(
                metadata.ProviderSymbol,
                metadata.Symbol,
                observationDate,
                asOfDate,
                decimal.Round(value.Value, 6, MidpointRounding.ToEven),
                metadata.Unit);
        }

        return null;
    }

    private static decimal? ValueAt(IReadOnlyList<decimal?>? values, int index)
    {
        return values is not null && index < values.Count
            ? values[index]
            : null;
    }

    private static long ToUnixSeconds(DateOnly date)
    {
        return new DateTimeOffset(date.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero).ToUnixTimeSeconds();
    }

    private static bool ShouldRetry(HttpStatusCode statusCode)
    {
        return statusCode is HttpStatusCode.TooManyRequests
            or HttpStatusCode.InternalServerError
            or HttpStatusCode.BadGateway
            or HttpStatusCode.ServiceUnavailable
            or HttpStatusCode.GatewayTimeout;
    }

    private sealed record YahooChartResponse(
        [property: JsonPropertyName("chart")] YahooChart? Chart);

    private sealed record YahooChart(
        [property: JsonPropertyName("result")] IReadOnlyList<YahooChartResult>? Result,
        [property: JsonPropertyName("error")] JsonElement? Error);

    private sealed record YahooChartResult(
        [property: JsonPropertyName("timestamp")] IReadOnlyList<long> Timestamp,
        [property: JsonPropertyName("indicators")] YahooIndicators? Indicators);

    private sealed record YahooIndicators(
        [property: JsonPropertyName("quote")] IReadOnlyList<YahooQuote>? Quote,
        [property: JsonPropertyName("adjclose")] IReadOnlyList<YahooAdjustedClose>? AdjClose);

    private sealed record YahooQuote(
        [property: JsonPropertyName("close")] IReadOnlyList<decimal?>? Close);

    private sealed record YahooAdjustedClose(
        [property: JsonPropertyName("adjclose")] IReadOnlyList<decimal?>? AdjClose);
}
