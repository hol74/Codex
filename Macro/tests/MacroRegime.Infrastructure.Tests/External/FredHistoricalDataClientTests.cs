using System.Net;
using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class FredHistoricalDataClientTests
{
    [Fact]
    public async Task FetchInitialReleaseHistoryAsync_UsesBulkInitialRelease_AndComputesYoY()
    {
        var handler = new FakeHandler(_ => JsonResponse("""
        {
          "count": 3,
          "observations": [
            { "realtime_start": "2023-02-15", "date": "2023-01-01", "value": "100" },
            { "realtime_start": "2024-02-15", "date": "2024-01-01", "value": "110" },
            { "realtime_start": "2025-02-15", "date": "2025-01-01", "value": "121" }
          ]
        }
        """));
        var client = new FredHistoricalDataClient(
            new HttpClient(handler),
            new FredHistoricalDataClientOptions("test-key") { BaseUri = new Uri("https://fred.test") });

        var observations = await client.FetchInitialReleaseHistoryAsync(
            new DateOnly(2024, 1, 1), new DateOnly(2025, 12, 31), new[] { "INDPRO_YOY" });

        Assert.Equal(2, observations.Count);
        Assert.All(observations, item => Assert.Equal(10m, item.Value));
        Assert.Equal(new DateOnly(2024, 2, 15), observations[0].PublicationDate);
        var uri = Assert.Single(handler.RequestUris);
        Assert.Contains("output_type=4", uri.Query);
        Assert.Contains("realtime_start=2022-01-01", uri.Query);
        Assert.Contains("limit=100000", uri.Query);
        Assert.DoesNotContain("units=pc1", uri.Query);
    }

    [Fact]
    public async Task FetchInitialReleaseHistoryAsync_UsesLongHistoryCreditSpreadProxy()
    {
        var handler = new FakeHandler(_ => JsonResponse("""
        {
          "count": 1,
          "observations": [
            { "realtime_start": "2008-04-30", "date": "2008-04-30", "value": "3.25" }
          ]
        }
        """));
        var client = new FredHistoricalDataClient(
            new HttpClient(handler),
            new FredHistoricalDataClientOptions("test-key") { BaseUri = new Uri("https://fred.test") });

        var observations = await client.FetchInitialReleaseHistoryAsync(
            new DateOnly(2008, 4, 1), new DateOnly(2008, 4, 30), new[] { "HY_OAS" });

        var observation = Assert.Single(observations);
        Assert.Equal("BAA10Y", observation.SeriesId);
        Assert.Equal("HY_OAS", observation.SeriesCode);
        Assert.Contains("series_id=BAA10Y", Assert.Single(handler.RequestUris).Query);
    }

    [Fact]
    public async Task FetchInitialReleaseHistoryAsync_ComputesCpiYoYFromInitialReleaseLevels()
    {
        var handler = new FakeHandler(_ => JsonResponse("""
        {
          "count": 3,
          "observations": [
            { "realtime_start": "2024-02-13", "date": "2024-01-01", "value": "100" },
            { "realtime_start": "2025-02-12", "date": "2025-01-01", "value": "103.5" },
            { "realtime_start": "2025-03-12", "date": "2025-01-01", "value": "105" }
          ]
        }
        """));
        var client = new FredHistoricalDataClient(
            new HttpClient(handler),
            new FredHistoricalDataClientOptions("test-key") { BaseUri = new Uri("https://fred.test") });

        var observations = await client.FetchInitialReleaseHistoryAsync(
            new DateOnly(2025, 1, 1), new DateOnly(2025, 12, 31), new[] { "CPI_YOY" });

        var observation = Assert.Single(observations);
        Assert.Equal("CPIAUCSL", observation.SeriesId);
        Assert.Equal("CPI_YOY", observation.SeriesCode);
        Assert.Equal(3.5m, observation.Value);
        Assert.Equal(new DateOnly(2025, 2, 12), observation.PublicationDate);
    }

    [Fact]
    public async Task FetchInitialReleaseHistoryAsync_FillsSahmReconstructionGapsFromOfficialRealtimeSeries()
    {
        var handler = new FakeHandler(request =>
            request.RequestUri!.Query.Contains("series_id=UNRATE", StringComparison.Ordinal)
                ? JsonResponse("""
                {
                  "count": 1,
                  "observations": [
                    { "realtime_start": "2026-06-05", "date": "2026-05-01", "value": "4.2" }
                  ]
                }
                """)
                : JsonResponse("""
                {
                  "count": 1,
                  "observations": [
                    { "realtime_start": "2026-06-05", "date": "2026-05-01", "value": "0.1" }
                  ]
                }
                """));
        var client = new FredHistoricalDataClient(
            new HttpClient(handler),
            new FredHistoricalDataClientOptions("test-key") { BaseUri = new Uri("https://fred.test") });

        var observations = await client.FetchInitialReleaseHistoryAsync(
            new DateOnly(2026, 5, 1), new DateOnly(2026, 6, 30), new[] { "SAHM" });

        var observation = Assert.Single(observations);
        Assert.Equal("SAHMREALTIME", observation.SeriesId);
        Assert.Equal("SAHM", observation.SeriesCode);
        Assert.Equal(0.1m, observation.Value);
        Assert.Equal(2, handler.RequestUris.Count);
        Assert.Contains(handler.RequestUris, uri => uri.Query.Contains("series_id=UNRATE", StringComparison.Ordinal));
        Assert.Contains(handler.RequestUris, uri => uri.Query.Contains("series_id=SAHMREALTIME", StringComparison.Ordinal));
        Assert.DoesNotContain(handler.RequestUris,
            uri => uri.Query.Contains("series_id=SAHMREALTIME", StringComparison.Ordinal)
                && uri.Query.Contains("output_type=4", StringComparison.Ordinal));
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
