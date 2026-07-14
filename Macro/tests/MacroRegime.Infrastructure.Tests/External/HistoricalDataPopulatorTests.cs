using System.Net;
using System.Text.Json;
using MacroRegime.Infrastructure.External;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class HistoricalDataPopulatorTests : IDisposable
{
    private readonly string directory = Path.Combine(Path.GetTempPath(), "HistoricalDataPopulatorTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task PopulateAsync_WritesMonthlyMacro_DailyMarket_AndCorpusManifest()
    {
        var fredHandler = new FakeHandler(request =>
        {
            var seriesId = QueryValue(request.RequestUri!, "series_id");
            var observations = seriesId is "INDPRO" or "CPIAUCSL"
                ? """
                  { "count": 5, "observations": [
                    { "realtime_start": "2023-02-15", "date": "2023-01-01", "value": "90" },
                    { "realtime_start": "2024-01-15", "date": "2023-12-01", "value": "95" },
                    { "realtime_start": "2024-02-15", "date": "2024-01-01", "value": "100" },
                    { "realtime_start": "2025-01-15", "date": "2024-12-01", "value": "104.5" },
                    { "realtime_start": "2025-02-15", "date": "2025-01-01", "value": "110" }
                  ] }
                  """
                : seriesId == "UNRATE"
                ? UnemploymentHistoryResponse()
                : """
                  { "count": 3, "observations": [
                    { "realtime_start": "2024-10-29", "date": "2024-10-29", "value": "0.5" },
                    { "realtime_start": "2025-01-29", "date": "2025-01-29", "value": "1" },
                    { "realtime_start": "2025-02-26", "date": "2025-02-26", "value": "2" }
                  ] }
                  """;
            return JsonResponse(observations);
        });
        var marketHandler = new FakeHandler(_ => JsonResponse("""
        {
          "chart": { "result": [{
            "timestamp": [1738195200, 1740614400, 1741564800],
            "indicators": {
              "quote": [{ "close": [100, 101, 102] }],
              "adjclose": [{ "adjclose": [100, 101, 102] }]
            }
          }] }
        }
        """));
        var populator = new HistoricalDataPopulator(
            new FredHistoricalDataClient(
                new HttpClient(fredHandler),
                new FredHistoricalDataClientOptions("key") { BaseUri = new Uri("https://fred.test") }),
            new YahooHistoricalMarketDataClient(
                new HttpClient(marketHandler),
                new YahooHistoricalMarketDataClientOptions { BaseUri = new Uri("https://yahoo.test") }));
        var macroDir = Path.Combine(directory, "macro");
        var marketDir = Path.Combine(directory, "market");
        var manifestPath = Path.Combine(directory, "corpus-manifest.json");

        var result = await populator.PopulateAsync(new PopulateHistoricalDataCommand(
            new DateOnly(2025, 1, 1), new DateOnly(2025, 2, 28), macroDir, marketDir, manifestPath, 1));

        Assert.Equal(2, result.MacroSnapshotCount);
        Assert.Equal(3, result.MarketSnapshotCount);
        Assert.Equal(new DateOnly(2025, 1, 30), result.FirstSampleDate);
        Assert.Equal(new DateOnly(2025, 2, 27), result.LastSampleDate);
        Assert.Equal(2, Directory.GetFiles(macroDir).Length);
        Assert.Equal(3, Directory.GetFiles(marketDir).Length);
        var manifest = JsonDocument.Parse(await File.ReadAllTextAsync(manifestPath));
        Assert.Equal(64, manifest.RootElement.GetProperty("aggregateSha256").GetString()!.Length);
        Assert.Equal("last-complete-trading-day-of-month", manifest.RootElement.GetProperty("sampling").GetString());
        Assert.Contains("CPI_YOY_3M_CHANGE", manifest.RootElement.GetProperty("macroSeries").EnumerateArray().Select(item => item.GetString()));
        var firstMacro = JsonDocument.Parse(await File.ReadAllTextAsync(
            Path.Combine(macroDir, "macro-data-2025-01-30.json")));
        var derivedCodes = firstMacro.RootElement.GetProperty("macroObservations").EnumerateArray()
            .Select(item => item.GetProperty("seriesCode").GetString())
            .ToArray();
        Assert.Contains("CPI_YOY_3M_CHANGE", derivedCodes);
        Assert.Contains("YC_10Y2Y_3M_CHANGE", derivedCodes);
        var curveChange = firstMacro.RootElement.GetProperty("macroObservations").EnumerateArray()
            .Single(item => item.GetProperty("seriesCode").GetString() == "YC_10Y2Y_3M_CHANGE");
        Assert.Equal(0.5m, curveChange.GetProperty("value").GetDecimal());
    }

    [Fact]
    public async Task PopulateAsync_RejectsStaleMonthlyMacroObservation()
    {
        var fredHandler = new FakeHandler(request =>
        {
            var seriesId = QueryValue(request.RequestUri!, "series_id");
            return seriesId is "INDPRO" or "CPIAUCSL"
                ? JsonResponse("""
                  { "count": 2, "observations": [
                    { "realtime_start": "2023-02-15", "date": "2023-01-01", "value": "100" },
                    { "realtime_start": "2024-02-15", "date": "2024-01-01", "value": "110" }
                  ] }
                  """)
                : seriesId == "UNRATE"
                    ? JsonResponse(UnemploymentHistoryResponse())
                    : JsonResponse("""
                      { "count": 1, "observations": [
                        { "realtime_start": "2025-02-26", "date": "2025-02-26", "value": "1" }
                      ] }
                      """);
        });
        var marketHandler = new FakeHandler(_ => JsonResponse("""
        {
          "chart": { "result": [{
            "timestamp": [1740614400],
            "indicators": {
              "quote": [{ "close": [101] }],
              "adjclose": [{ "adjclose": [101] }]
            }
          }] }
        }
        """));
        var populator = new HistoricalDataPopulator(
            new FredHistoricalDataClient(
                new HttpClient(fredHandler),
                new FredHistoricalDataClientOptions("key") { BaseUri = new Uri("https://fred.test") }),
            new YahooHistoricalMarketDataClient(
                new HttpClient(marketHandler),
                new YahooHistoricalMarketDataClientOptions { BaseUri = new Uri("https://yahoo.test") }));

        var exception = await Assert.ThrowsAsync<InvalidDataException>(() => populator.PopulateAsync(
            new PopulateHistoricalDataCommand(
                new DateOnly(2025, 2, 1),
                new DateOnly(2025, 2, 28),
                Path.Combine(directory, "stale-macro"),
                Path.Combine(directory, "stale-market"),
                Path.Combine(directory, "stale-manifest.json"),
                1)));

        Assert.Contains("Stale monthly FRED observation for 'INDPRO_YOY'", exception.Message);
        Assert.Contains("13 months old", exception.Message);
    }

    public void Dispose()
    {
        if (Directory.Exists(directory))
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static string QueryValue(Uri uri, string name)
    {
        return uri.Query.TrimStart('?').Split('&')
            .Select(part => part.Split('=', 2))
            .Where(parts => parts.Length == 2)
            .First(parts => Uri.UnescapeDataString(parts[0]) == name)
            .Select(Uri.UnescapeDataString)
            .Last();
    }

    private static string UnemploymentHistoryResponse()
    {
        var observations = Enumerable.Range(0, 18)
            .Select(index => new
            {
                realtime_start = new DateOnly(2023, 9, 5).AddMonths(index).ToString("yyyy-MM-dd"),
                date = new DateOnly(2023, 8, 1).AddMonths(index).ToString("yyyy-MM-dd"),
                value = (4m + (index * 0.1m)).ToString(System.Globalization.CultureInfo.InvariantCulture),
            })
            .ToArray();
        return JsonSerializer.Serialize(new { count = observations.Length, observations });
    }

    private static HttpResponseMessage JsonResponse(string json) => new(HttpStatusCode.OK)
    {
        Content = new StringContent(json),
    };

    private sealed class FakeHandler(Func<HttpRequestMessage, HttpResponseMessage> handler) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken) =>
            Task.FromResult(handler(request));
    }
}
