using System.Net;
using MacroRegime.Application.External;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class YahooMarketDataSourceTests
{
    private static readonly AsOfDate AsOf = new(new DateOnly(2026, 7, 1));

    [Fact]
    public async Task FetchAsync_RequestsYahooChartEndpoint_AndMapsAdjustedClose()
    {
        var handler = new FakeHttpMessageHandler(_ => JsonResponse("""
        {
          "chart": {
            "result": [
              {
                "timestamp": [1782777600, 1782864000],
                "indicators": {
                  "quote": [ { "close": [510.0, 511.0] } ],
                  "adjclose": [ { "adjclose": [509.5, 510.75] } ]
                }
              }
            ],
            "error": null
          }
        }
        """));
        var source = CreateSource(handler);

        var result = await source.FetchAsync(new MarketDataFetchCommand(AsOf, new MarketDataSeriesSet(new[] { "SPY" })));

        var observation = Assert.Single(result);
        Assert.Equal("SPY", observation.ProviderSymbol);
        Assert.Equal("SPY", observation.Symbol);
        Assert.Equal(new DateOnly(2026, 7, 1), observation.ObservationDate);
        Assert.Equal(new DateOnly(2026, 7, 1), observation.AvailabilityDate);
        Assert.Equal(510.75m, observation.Value);
        Assert.Equal("Adjusted close", observation.Unit);

        var uri = Assert.Single(handler.RequestUris);
        Assert.Equal("/v8/finance/chart/SPY", uri.AbsolutePath);
        Assert.Contains("interval=1d", uri.Query);
        Assert.Contains("events=history", uri.Query);
        Assert.Contains("includeAdjustedClose=true", uri.Query);
    }

    [Fact]
    public async Task FetchAsync_FallsBackToClose_WhenAdjustedCloseIsMissing()
    {
        var handler = new FakeHttpMessageHandler(_ => JsonResponse("""
        {
          "chart": {
            "result": [
              {
                "timestamp": [1782864000],
                "indicators": {
                  "quote": [ { "close": [511.0] } ]
                }
              }
            ],
            "error": null
          }
        }
        """));
        var source = CreateSource(handler);

        var result = await source.FetchAsync(new MarketDataFetchCommand(AsOf, new MarketDataSeriesSet(new[] { "SPY" })));

        Assert.Equal(511.0m, Assert.Single(result).Value);
    }

    [Fact]
    public async Task FetchAsync_SkipsNullValues_AndUsesLatestUsableClose()
    {
        var handler = new FakeHttpMessageHandler(_ => JsonResponse("""
        {
          "chart": {
            "result": [
              {
                "timestamp": [1782777600, 1782864000],
                "indicators": {
                  "quote": [ { "close": [510.0, null] } ],
                  "adjclose": [ { "adjclose": [509.5, null] } ]
                }
              }
            ],
            "error": null
          }
        }
        """));
        var source = CreateSource(handler);

        var result = await source.FetchAsync(new MarketDataFetchCommand(AsOf, new MarketDataSeriesSet(new[] { "SPY" })));

        var observation = Assert.Single(result);
        Assert.Equal(new DateOnly(2026, 6, 30), observation.ObservationDate);
        Assert.Equal(509.5m, observation.Value);
    }

    [Fact]
    public async Task FetchAsync_RetriesTransientStatusCode()
    {
        var attempts = 0;
        var handler = new FakeHttpMessageHandler(_ =>
        {
            attempts++;
            return attempts == 1
                ? new HttpResponseMessage(HttpStatusCode.TooManyRequests) { Content = new StringContent("rate limited") }
                : JsonResponse("""
                  {
                    "chart": {
                      "result": [
                        {
                          "timestamp": [1782864000],
                          "indicators": {
                            "quote": [ { "close": [511.0] } ],
                            "adjclose": [ { "adjclose": [510.75] } ]
                          }
                        }
                      ],
                      "error": null
                    }
                  }
                  """);
        });
        var source = CreateSource(handler, new YahooMarketDataSourceOptions
        {
            BaseUri = new Uri("https://yahoo.test"),
            MaxAttempts = 2,
            RetryDelay = TimeSpan.Zero,
        });

        var result = await source.FetchAsync(new MarketDataFetchCommand(AsOf, new MarketDataSeriesSet(new[] { "SPY" })));

        Assert.Equal(2, attempts);
        Assert.Single(result);
    }

    [Fact]
    public void Constructor_Throws_WhenOptionsAreInvalid()
    {
        var handler = new FakeHttpMessageHandler(_ => JsonResponse("""{}"""));

        Assert.Throws<ArgumentException>(() =>
            CreateSource(handler, new YahooMarketDataSourceOptions { MaxAttempts = 0 }));
    }

    private static YahooMarketDataSource CreateSource(
        FakeHttpMessageHandler handler,
        YahooMarketDataSourceOptions? options = null)
    {
        return new YahooMarketDataSource(
            new HttpClient(handler),
            options ?? new YahooMarketDataSourceOptions { BaseUri = new Uri("https://yahoo.test") });
    }

    private static HttpResponseMessage JsonResponse(string json)
    {
        return new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(json),
        };
    }

    private sealed class FakeHttpMessageHandler(Func<HttpRequestMessage, HttpResponseMessage> handler) : HttpMessageHandler
    {
        public List<Uri> RequestUris { get; } = new();

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            RequestUris.Add(request.RequestUri!);
            return Task.FromResult(handler(request));
        }
    }
}
