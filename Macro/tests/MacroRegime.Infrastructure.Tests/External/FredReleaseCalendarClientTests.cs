using System.Net;
using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class FredReleaseCalendarClientTests
{
    [Fact]
    public async Task FetchAllReleaseDatesAsync_RequestsGlobalReleaseCalendar_AndMapsDates()
    {
        var handler = new FakeHttpMessageHandler(_ => JsonResponse("""
        {
          "release_dates": [
            { "release_id": 53, "release_name": "Gross Domestic Product", "date": "2026-07-30" },
            { "release_id": 82, "release_name": "Regional and State Employment and Unemployment", "date": "2026-07-31" }
          ]
        }
        """));
        var client = CreateClient(handler);

        var result = await client.FetchAllReleaseDatesAsync(new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 31));

        Assert.Equal(2, result.Count);
        Assert.Contains(result, item => item.ReleaseId == 53 && item.ReleaseName == "Gross Domestic Product" && item.Date == new DateOnly(2026, 7, 30));
        var uri = Assert.Single(handler.RequestUris);
        Assert.Equal("/fred/releases/dates", uri.AbsolutePath);
        Assert.Contains("api_key=test-key", uri.Query);
        Assert.Contains("file_type=json", uri.Query);
        Assert.Contains("realtime_start=2026-07-01", uri.Query);
        Assert.Contains("realtime_end=2026-07-31", uri.Query);
        Assert.Contains("include_release_dates_with_no_data=false", uri.Query);
        Assert.Contains("order_by=release_date", uri.Query);
        Assert.Contains("sort_order=asc", uri.Query);
    }

    [Fact]
    public async Task FetchReleaseDatesAsync_RequestsSpecificReleaseCalendar()
    {
        var handler = new FakeHttpMessageHandler(_ => JsonResponse("""
        {
          "release_dates": [
            { "release_id": 82, "date": "2026-07-17" }
          ]
        }
        """));
        var client = CreateClient(handler);

        var result = await client.FetchReleaseDatesAsync(
            82,
            new DateOnly(2026, 7, 1),
            new DateOnly(2026, 7, 31),
            includeReleaseDatesWithNoData: true);

        var releaseDate = Assert.Single(result);
        Assert.Equal(82, releaseDate.ReleaseId);
        Assert.Null(releaseDate.ReleaseName);
        Assert.Equal(new DateOnly(2026, 7, 17), releaseDate.Date);
        var uri = Assert.Single(handler.RequestUris);
        Assert.Equal("/fred/release/dates", uri.AbsolutePath);
        Assert.Contains("release_id=82", uri.Query);
        Assert.Contains("include_release_dates_with_no_data=true", uri.Query);
    }

    [Fact]
    public async Task FetchAllReleaseDatesAsync_RetriesTransientStatusCode()
    {
        var attempts = 0;
        var handler = new FakeHttpMessageHandler(_ =>
        {
            attempts++;
            return attempts == 1
                ? new HttpResponseMessage(HttpStatusCode.ServiceUnavailable) { Content = new StringContent("try later") }
                : JsonResponse("""{ "release_dates": [] }""");
        });
        var client = CreateClient(handler, new FredReleaseCalendarOptions("test-key")
        {
            BaseUri = new Uri("https://fred.test"),
            MaxAttempts = 2,
            RetryDelay = TimeSpan.Zero,
        });

        var result = await client.FetchAllReleaseDatesAsync(new DateOnly(2026, 7, 1), new DateOnly(2026, 7, 31));

        Assert.Equal(2, attempts);
        Assert.Empty(result);
    }

    [Fact]
    public void Constructor_Throws_WhenApiKeyIsMissing()
    {
        var handler = new FakeHttpMessageHandler(_ => JsonResponse("""{ "release_dates": [] }"""));

        Assert.Throws<ArgumentException>(() =>
            CreateClient(handler, new FredReleaseCalendarOptions(" ")));
    }

    private static FredReleaseCalendarClient CreateClient(
        FakeHttpMessageHandler handler,
        FredReleaseCalendarOptions? options = null)
    {
        return new FredReleaseCalendarClient(
            new HttpClient(handler),
            options ?? new FredReleaseCalendarOptions("test-key") { BaseUri = new Uri("https://fred.test") });
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
