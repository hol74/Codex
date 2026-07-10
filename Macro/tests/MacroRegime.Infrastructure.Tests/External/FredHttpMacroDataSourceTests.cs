using System.Net;
using MacroRegime.Application.External;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class FredHttpMacroDataSourceTests
{
    private static readonly AsOfDate AsOf = new(new DateOnly(2026, 7, 1));

    [Fact]
    public async Task FetchAsync_RequestsFredObservationEndpoint_WithApiKeyAndAsOfDate()
    {
        var handler = new FakeHttpMessageHandler(request => request.RequestUri!.AbsolutePath switch
        {
            "/fred/series/vintagedates" => JsonResponse("""{ "vintage_dates": [ "2026-06-28" ] }"""),
            "/fred/series/observations" => JsonResponse("""
            {
              "observations": [
                { "realtime_start": "2026-06-28", "realtime_end": "2026-06-28", "date": "2026-06-30", "value": "18.45" }
              ]
            }
            """),
            _ => new HttpResponseMessage(HttpStatusCode.NotFound),
        });
        var source = CreateSource(handler);

        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "VIX" })));

        var observation = Assert.Single(result);
        Assert.Equal("VIXCLS", observation.SeriesId);
        Assert.Equal("VIX", observation.SeriesCode);
        Assert.Equal(new DateOnly(2026, 6, 30), observation.ObservationDate);
        Assert.Equal(18.45m, observation.Value);
        Assert.Equal(new DateOnly(2026, 6, 28), observation.PublicationDate);
        Assert.Equal(new DateOnly(2026, 6, 28), observation.VintageDate);

        Assert.Equal(2, handler.RequestUris.Count);
        var vintageRequestUri = handler.RequestUris[0];
        Assert.Equal("/fred/series/vintagedates", vintageRequestUri.AbsolutePath);
        Assert.Contains("series_id=VIXCLS", vintageRequestUri.Query);
        Assert.Contains("api_key=test-key", vintageRequestUri.Query);
        Assert.Contains("file_type=json", vintageRequestUri.Query);
        Assert.Contains("sort_order=desc", vintageRequestUri.Query);
        Assert.Contains("limit=1", vintageRequestUri.Query);
        Assert.Contains("realtime_end=2026-07-01", vintageRequestUri.Query);

        var observationsRequestUri = handler.RequestUris[1];
        Assert.Equal("/fred/series/observations", observationsRequestUri.AbsolutePath);
        Assert.Contains("series_id=VIXCLS", observationsRequestUri.Query);
        Assert.Contains("api_key=test-key", observationsRequestUri.Query);
        Assert.Contains("file_type=json", observationsRequestUri.Query);
        Assert.Contains("sort_order=desc", observationsRequestUri.Query);
        Assert.Contains("limit=30", observationsRequestUri.Query);
        Assert.Contains("observation_end=2026-07-01", observationsRequestUri.Query);
        Assert.Contains("vintage_dates=2026-06-28", observationsRequestUri.Query);
    }

    [Fact]
    public async Task FetchAsync_SkipsMissingDotValues_AndUsesLatestUsableObservation()
    {
        var handler = new FakeHttpMessageHandler(request => request.RequestUri!.AbsolutePath switch
        {
            "/fred/series/vintagedates" => JsonResponse("""{ "vintage_dates": [ "2026-07-01" ] }"""),
            "/fred/series/observations" => JsonResponse("""
            {
              "observations": [
                { "realtime_start": "2026-07-01", "realtime_end": "2026-07-01", "date": "2026-07-01", "value": "." },
                { "realtime_start": "2026-07-01", "realtime_end": "2026-07-01", "date": "2026-06-30", "value": "2.23" }
              ]
            }
            """),
            _ => new HttpResponseMessage(HttpStatusCode.NotFound),
        });
        var source = CreateSource(handler);

        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "T10YIE" })));

        var observation = Assert.Single(result);
        Assert.Equal(new DateOnly(2026, 6, 30), observation.ObservationDate);
        Assert.Equal(2.23m, observation.Value);
    }

    [Fact]
    public async Task FetchAsync_ThrowsInvalidData_WhenNoUsableObservationExists()
    {
        var handler = new FakeHttpMessageHandler(request => request.RequestUri!.AbsolutePath switch
        {
            "/fred/series/vintagedates" => JsonResponse("""{ "vintage_dates": [ "2026-07-01" ] }"""),
            "/fred/series/observations" => JsonResponse("""
            {
              "observations": [
                { "realtime_start": "2026-07-01", "realtime_end": "2026-07-01", "date": "2026-07-01", "value": "." }
              ]
            }
            """),
            _ => new HttpResponseMessage(HttpStatusCode.NotFound),
        });
        var source = CreateSource(handler);

        await Assert.ThrowsAsync<InvalidDataException>(() =>
            source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "VIX" }))));
    }

    [Fact]
    public async Task FetchAsync_RetriesTransientStatusCode()
    {
        var attempts = 0;
        var handler = new FakeHttpMessageHandler(request =>
        {
            if (request.RequestUri!.AbsolutePath == "/fred/series/vintagedates")
            {
                return JsonResponse("""{ "vintage_dates": [ "2026-07-01" ] }""");
            }

            attempts++;
            return attempts == 1
                ? new HttpResponseMessage(HttpStatusCode.TooManyRequests) { Content = new StringContent("rate limited") }
                : JsonResponse("""
                  {
                    "observations": [
                      { "realtime_start": "2026-07-01", "realtime_end": "2026-07-01", "date": "2026-07-01", "value": "18.45" }
                    ]
                  }
                  """);
        });
        var source = CreateSource(handler, new FredHttpMacroDataSourceOptions("test-key")
        {
            BaseUri = new Uri("https://fred.test"),
            MaxAttempts = 2,
            RetryDelay = TimeSpan.Zero,
        });

        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "VIX" })));

        Assert.Equal(2, attempts);
        Assert.Single(result);
    }

    [Fact]
    public async Task FetchAsync_ThrowsInvalidData_WhenNoVintageDateExists()
    {
        var handler = new FakeHttpMessageHandler(_ => JsonResponse("""{ "vintage_dates": [] }"""));
        var source = CreateSource(handler);

        await Assert.ThrowsAsync<InvalidDataException>(() =>
            source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "VIX" }))));
    }

    [Fact]
    public async Task FetchAsync_FallsBackToFredObservation_WhenSeriesIsNotInAlfred()
    {
        var handler = new FakeHttpMessageHandler(request => request.RequestUri!.AbsolutePath switch
        {
            "/fred/series/vintagedates" => new HttpResponseMessage(HttpStatusCode.BadRequest)
            {
                Content = new StringContent("""
                {"error_code":400,"error_message":"Bad Request. The series does not exist in ALFRED but may exist in FRED."}
                """),
            },
            "/fred/series/observations" => JsonResponse("""
            {
              "observations": [
                { "realtime_start": "2026-07-01", "realtime_end": "2026-07-01", "date": "2026-06-01", "value": "52.8" }
              ]
            }
            """),
            _ => new HttpResponseMessage(HttpStatusCode.NotFound),
        });
        var source = CreateSource(handler);

        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "INDPRO_YOY" })));

        var observation = Assert.Single(result);
        Assert.Equal("INDPRO", observation.SeriesId);
        Assert.Equal("Percent change", observation.Unit);
        Assert.Equal(52.8m, observation.Value);
        Assert.Equal(2, handler.RequestUris.Count);
        Assert.Contains("units=pc1", handler.RequestUris[1].Query);
        Assert.DoesNotContain("vintage_dates", handler.RequestUris[1].Query);
    }

    [Fact]
    public void Constructor_Throws_WhenApiKeyIsMissing()
    {
        var handler = new FakeHttpMessageHandler(_ => JsonResponse("""{ "observations": [] }"""));

        Assert.Throws<ArgumentException>(() =>
            CreateSource(handler, new FredHttpMacroDataSourceOptions(" ")));
    }

    private static FredHttpMacroDataSource CreateSource(
        FakeHttpMessageHandler handler,
        FredHttpMacroDataSourceOptions? options = null)
    {
        return new FredHttpMacroDataSource(
            new HttpClient(handler),
            options ?? new FredHttpMacroDataSourceOptions("test-key") { BaseUri = new Uri("https://fred.test") });
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
