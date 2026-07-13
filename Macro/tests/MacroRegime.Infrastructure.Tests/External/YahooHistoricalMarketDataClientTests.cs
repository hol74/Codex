using System.Net;
using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class YahooHistoricalMarketDataClientTests
{
    [Fact]
    public async Task FetchHistoryAsync_UsesSingleRangeRequestPerSymbol_AndMapsAdjustedClose()
    {
        var handler = new FakeHandler(_ => JsonResponse("""
        {
          "chart": {
            "result": [{
              "timestamp": [1738195200, 1738281600],
              "indicators": {
                "quote": [{ "close": [100.0, 102.0] }],
                "adjclose": [{ "adjclose": [99.5, 101.5] }]
              }
            }]
          }
        }
        """));
        var client = new YahooHistoricalMarketDataClient(
            new HttpClient(handler),
            new YahooHistoricalMarketDataClientOptions { BaseUri = new Uri("https://yahoo.test") });

        var observations = await client.FetchHistoryAsync(
            new DateOnly(2025, 1, 30), new DateOnly(2025, 1, 31), new[] { "SPY" });

        Assert.Equal(2, observations.Count);
        Assert.Equal(99.5m, observations[0].Value);
        Assert.Equal(101.5m, observations[1].Value);
        var uri = Assert.Single(handler.RequestUris);
        Assert.Contains("interval=1d", uri.Query);
        Assert.Contains("includeAdjustedClose=true", uri.Query);
    }

    private static HttpResponseMessage JsonResponse(string json) => new(HttpStatusCode.OK)
    {
        Content = new StringContent(json),
    };

    private sealed class FakeHandler(Func<HttpRequestMessage, HttpResponseMessage> handler) : HttpMessageHandler
    {
        public List<Uri> RequestUris { get; } = new();

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            RequestUris.Add(request.RequestUri!);
            return Task.FromResult(handler(request));
        }
    }
}

