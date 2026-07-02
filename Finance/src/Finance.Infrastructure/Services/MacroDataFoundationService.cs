using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Finance.Application.MacroRegime;
using Finance.Domain.Entities;
using Finance.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace Finance.Infrastructure.Services;

public sealed class MacroDataFoundationService(FinanceDbContext dbContext, HttpClient httpClient) : IMacroDataFoundationService
{
    public async Task<MacroDataFoundationDashboard> GetDashboardAsync(DateOnly? asOfDate = null, CancellationToken cancellationToken = default)
    {
        var snapshotDate = asOfDate ?? DateOnly.FromDateTime(DateTime.Today);
        var snapshot = await GetAsOfSnapshotAsync(snapshotDate, cancellationToken);

        var dataSources = await dbContext.MacroDataSources
            .AsNoTracking()
            .Include(x => x.Series)
            .Include(x => x.MarketSeries)
            .OrderBy(x => x.Name)
            .Select(x => new MacroDataSourceCatalogItem(
                x.Name,
                x.Kind,
                x.SupportsVintageData,
                x.Series.Count,
                x.MarketSeries.Count,
                x.Url))
            .ToListAsync(cancellationToken);

        var macroSeriesRows = await dbContext.MacroSeries
            .AsNoTracking()
            .Include(x => x.MacroDataSource)
            .Include(x => x.Observations)
            .Include(x => x.Vintages)
            .OrderBy(x => x.Category)
            .ThenBy(x => x.Code)
            .ToListAsync(cancellationToken);

        var macroSeries = macroSeriesRows
            .Select(x => new MacroSeriesCatalogItem(
                x.Code,
                x.Name,
                x.Category,
                x.Frequency,
                x.MacroDataSource?.Name ?? "Unknown",
                x.RequiresVintageTracking,
                x.Observations.Count,
                x.Observations.OrderByDescending(y => y.ObservationDate).Select(y => (DateOnly?)y.ObservationDate).FirstOrDefault(),
                x.Vintages.OrderByDescending(y => y.VintageDate).Select(y => (DateOnly?)y.VintageDate).FirstOrDefault()))
            .ToList();

        var marketSeriesRows = await dbContext.MarketSeries
            .AsNoTracking()
            .Include(x => x.MacroDataSource)
            .Include(x => x.Observations)
            .OrderBy(x => x.Category)
            .ThenBy(x => x.Symbol)
            .ToListAsync(cancellationToken);

        var marketSeries = marketSeriesRows
            .Select(x => new MarketSeriesCatalogItem(
                x.Symbol,
                x.Name,
                x.Category,
                x.Frequency,
                x.MacroDataSource?.Name ?? "Unknown",
                x.ProxyRole,
                x.Observations.Count,
                x.Observations.OrderByDescending(y => y.Date).Select(y => (DateOnly?)y.Date).FirstOrDefault(),
                x.Observations.OrderByDescending(y => y.AvailableDate).Select(y => (DateOnly?)y.AvailableDate).FirstOrDefault()))
            .ToList();

        var releases = await dbContext.ReleaseCalendar
            .AsNoTracking()
            .Include(x => x.MacroDataSource)
            .OrderByDescending(x => x.ReleaseDate)
            .Take(20)
            .Select(x => new ReleaseCalendarCatalogItem(
                x.ReleaseCode,
                x.Name,
                x.MacroDataSource != null ? x.MacroDataSource.Name : "Unknown",
                x.ReleaseDate,
                x.Frequency,
                x.Status))
            .ToListAsync(cancellationToken);

        var importBatchRows = await dbContext.ImportBatches
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        var importBatches = importBatchRows
            .OrderByDescending(x => x.ImportedAt)
            .Take(20)
            .Select(x => new ImportBatchCatalogItem(
                x.ImportedAt,
                x.SourceName,
                x.RecordsRead,
                x.RecordsAccepted,
                x.RecordsRejected,
                x.FileName))
            .ToList();

        return new MacroDataFoundationDashboard(snapshotDate, dataSources, macroSeries, marketSeries, releases, importBatches, snapshot);
    }

    public async Task<MacroDataImportResult> ImportFredObservationsAsync(FredObservationImportRequest request, CancellationToken cancellationToken = default)
    {
        var source = await EnsureMacroDataSourceAsync("FRED", "MacroApi", "https://fred.stlouisfed.org", "https://api.stlouisfed.org/fred", true, cancellationToken);
        var series = await EnsureMacroSeriesAsync(source, request.SeriesCode, request.SeriesCode, "Macro", "Unknown", null, true, request.SeriesCode, null, cancellationToken);
        var url = BuildFredObservationUrl(request);
        using var response = await httpClient.GetAsync(url, cancellationToken);
        var payload = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            return new MacroDataImportResult("FRED", 0, 0, 0, [$"FRED import failed: {(int)response.StatusCode} {response.ReasonPhrase}"]);
        }

        var importBatch = dbContext.ImportBatches.Add(new ImportBatch
        {
            SourceName = "FRED",
            RecordsRead = 0,
            RecordsAccepted = 0,
            RecordsRejected = 0,
            FileName = $"fred:{request.SeriesCode}"
        }).Entity;

        var sourceHash = Hash(payload);
        var vintage = await EnsureDataVintageAsync(
            series,
            importBatch,
            request.RealtimeEnd,
            request.RealtimeStart,
            request.RealtimeEnd,
            "FRED",
            url,
            sourceHash,
            isOfficialVintage: true,
            cancellationToken);

        var accepted = 0;
        var rejected = 0;
        using var document = JsonDocument.Parse(payload);
        var observations = document.RootElement.GetProperty("observations").EnumerateArray().ToList();

        foreach (var item in observations)
        {
            var valueText = item.GetProperty("value").GetString();
            if (string.IsNullOrWhiteSpace(valueText) || valueText == "." || !decimal.TryParse(valueText, NumberStyles.Any, CultureInfo.InvariantCulture, out var value))
            {
                rejected++;
                continue;
            }

            var observationDate = DateOnly.ParseExact(item.GetProperty("date").GetString()!, "yyyy-MM-dd", CultureInfo.InvariantCulture);
            var publishedDate = DateOnly.ParseExact(item.GetProperty("realtime_start").GetString()!, "yyyy-MM-dd", CultureInfo.InvariantCulture);
            await UpsertMacroObservationAsync(series, vintage, observationDate, publishedDate, value, request.RealtimeEnd.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture), cancellationToken);
            accepted++;
        }

        importBatch.RecordsRead = observations.Count;
        importBatch.RecordsAccepted = accepted;
        importBatch.RecordsRejected = rejected;
        await dbContext.SaveChangesAsync(cancellationToken);

        return new MacroDataImportResult("FRED", observations.Count, accepted, rejected, [$"Imported {accepted} observations for {request.SeriesCode}."]);
    }

    public async Task<MacroDataImportResult> ImportFredMdCsvAsync(FredMdCsvImportRequest request, CancellationToken cancellationToken = default)
    {
        var source = await EnsureMacroDataSourceAsync("FRED-MD", "MacroDataset", "https://research.stlouisfed.org/econ/mccracken/fred-databases/", null, true, cancellationToken);
        var rows = ParseCsv(request.CsvContent);
        if (rows.Count == 0)
        {
            return new MacroDataImportResult("FRED-MD", 0, 0, 0, ["CSV FRED-MD vuoto."]);
        }

        var header = rows[0];
        var dateIndex = Array.FindIndex(header, x => string.Equals(x, "sasdate", StringComparison.OrdinalIgnoreCase) || string.Equals(x, "date", StringComparison.OrdinalIgnoreCase));
        if (dateIndex < 0)
        {
            return new MacroDataImportResult("FRED-MD", rows.Count - 1, 0, rows.Count - 1, ["CSV FRED-MD senza colonna sasdate/date."]);
        }

        var importBatch = dbContext.ImportBatches.Add(new ImportBatch
        {
            SourceName = "FRED-MD",
            RecordsRead = rows.Count - 1,
            RecordsAccepted = 0,
            RecordsRejected = 0,
            FileName = $"fred-md:{request.VintageDate:yyyy-MM-dd}"
        }).Entity;

        var accepted = 0;
        var rejected = 0;
        var sourceHash = Hash(request.CsvContent);

        for (var column = 0; column < header.Length; column++)
        {
            if (column == dateIndex || !request.ColumnToSeriesCode.TryGetValue(header[column], out var seriesCode))
            {
                continue;
            }

            var series = await EnsureMacroSeriesAsync(source, seriesCode, header[column], "Macro", "Monthly", null, true, null, header[column], cancellationToken);
            var vintage = await EnsureDataVintageAsync(series, importBatch, request.VintageDate, request.VintageDate, request.VintageDate, "FRED-MD", null, sourceHash, true, cancellationToken);

            foreach (var row in rows.Skip(1))
            {
                if (row.Length <= Math.Max(column, dateIndex))
                {
                    rejected++;
                    continue;
                }

                if (!TryParseFredMdDate(row[dateIndex], out var observationDate) ||
                    !decimal.TryParse(row[column], NumberStyles.Any, CultureInfo.InvariantCulture, out var value))
                {
                    rejected++;
                    continue;
                }

                await UpsertMacroObservationAsync(series, vintage, observationDate, request.PublishedDate, value, request.VintageDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture), cancellationToken);
                accepted++;
            }
        }

        importBatch.RecordsAccepted = accepted;
        importBatch.RecordsRejected = rejected;
        await dbContext.SaveChangesAsync(cancellationToken);

        return new MacroDataImportResult("FRED-MD", rows.Count - 1, accepted, rejected, [$"Imported {accepted} FRED-MD values from vintage {request.VintageDate:yyyy-MM-dd}."]);
    }

    public async Task<MacroDataImportResult> ImportMarketObservationsAsync(MarketObservationImportRequest request, CancellationToken cancellationToken = default)
    {
        var source = await EnsureMacroDataSourceAsync(request.SourceSystem, "MarketData", null, null, false, cancellationToken);
        var series = await EnsureMarketSeriesAsync(source, request.Symbol, request.Symbol, "Market", "Daily", null, cancellationToken);
        var accepted = 0;

        foreach (var input in request.Observations)
        {
            var existing = await dbContext.MarketObservations.FirstOrDefaultAsync(x => x.MarketSeriesId == series.Id && x.Date == input.Date, cancellationToken);
            if (existing is not null)
            {
                existing.Value = input.Value;
                existing.AvailableDate = input.AvailableDate;
                existing.SourceHash = input.SourceHash;
                existing.Notes = input.Notes;
                existing.UpdatedAt = DateTimeOffset.UtcNow;
            }
            else
            {
                dbContext.MarketObservations.Add(new MarketObservation
                {
                    MarketSeries = series,
                    Date = input.Date,
                    Value = input.Value,
                    AvailableDate = input.AvailableDate,
                    SourceHash = input.SourceHash,
                    Notes = input.Notes
                });
            }

            accepted++;
        }

        await dbContext.SaveChangesAsync(cancellationToken);
        return new MacroDataImportResult(request.SourceSystem, request.Observations.Count, accepted, 0, [$"Imported {accepted} market observations for {request.Symbol}."]);
    }

    public async Task<AsOfDataSnapshot> GetAsOfSnapshotAsync(DateOnly asOfDate, CancellationToken cancellationToken = default)
    {
        var macroRows = await dbContext.MacroObservations
            .AsNoTracking()
            .Include(x => x.MacroSeries)
            .ThenInclude(x => x!.MacroDataSource)
            .Include(x => x.DataVintage)
            .Where(x => x.PublishedDate <= asOfDate && (x.DataVintage == null || x.DataVintage.VintageDate <= asOfDate))
            .ToListAsync(cancellationToken);

        var macro = macroRows
            .GroupBy(x => x.MacroSeriesId)
            .Select(x => x
                .OrderByDescending(y => y.ObservationDate)
                .ThenByDescending(y => y.DataVintage != null ? y.DataVintage.VintageDate : DateOnly.MinValue)
                .First())
            .OrderBy(x => x.MacroSeries!.Category)
            .ThenBy(x => x.MacroSeries!.Code)
            .Select(x => new AsOfMacroObservation(
                x.MacroSeries!.Code,
                x.MacroSeries.Name,
                x.MacroSeries.Category,
                x.ObservationDate,
                x.PublishedDate,
                x.DataVintage?.VintageDate ?? (DateOnly.TryParse(x.Vintage, out var parsed) ? parsed : x.PublishedDate),
                x.Value,
                x.DataVintage?.SourceSystem ?? x.MacroSeries.MacroDataSource?.Name ?? "Unknown"))
            .ToList();

        var marketRows = await dbContext.MarketObservations
            .AsNoTracking()
            .Include(x => x.MarketSeries)
            .ThenInclude(x => x!.MacroDataSource)
            .Where(x => x.AvailableDate <= asOfDate)
            .ToListAsync(cancellationToken);

        var market = marketRows
            .GroupBy(x => x.MarketSeriesId)
            .Select(x => x.OrderByDescending(y => y.Date).First())
            .OrderBy(x => x.MarketSeries!.Category)
            .ThenBy(x => x.MarketSeries!.Symbol)
            .Select(x => new AsOfMarketObservation(
                x.MarketSeries!.Symbol,
                x.MarketSeries.Name,
                x.MarketSeries.Category,
                x.Date,
                x.AvailableDate,
                x.Value,
                x.MarketSeries.MacroDataSource?.Name ?? "Unknown"))
            .ToList();

        return new AsOfDataSnapshot(asOfDate, macro, market);
    }

    private async Task<MacroDataSource> EnsureMacroDataSourceAsync(string name, string kind, string? url, string? apiBaseUrl, bool supportsVintage, CancellationToken cancellationToken)
    {
        var existing = await dbContext.MacroDataSources.FirstOrDefaultAsync(x => x.Name == name, cancellationToken);
        if (existing is not null)
        {
            return existing;
        }

        return dbContext.MacroDataSources.Add(new MacroDataSource
        {
            Name = name,
            Kind = kind,
            Url = url,
            ApiBaseUrl = apiBaseUrl,
            SupportsVintageData = supportsVintage
        }).Entity;
    }

    private async Task<MacroSeries> EnsureMacroSeriesAsync(MacroDataSource source, string code, string name, string category, string frequency, string? unit, bool isHigherRiskOn, string? fredSeriesId, string? fredMdColumn, CancellationToken cancellationToken)
    {
        var existing = await dbContext.MacroSeries.FirstOrDefaultAsync(x => x.Code == code, cancellationToken);
        if (existing is not null)
        {
            return existing;
        }

        return dbContext.MacroSeries.Add(new MacroSeries
        {
            MacroDataSource = source,
            Code = code,
            Name = name,
            Category = category,
            Frequency = frequency,
            Unit = unit,
            IsHigherRiskOn = isHigherRiskOn,
            FredSeriesId = fredSeriesId,
            FredMdColumn = fredMdColumn,
            RequiresVintageTracking = true
        }).Entity;
    }

    private async Task<MarketSeries> EnsureMarketSeriesAsync(MacroDataSource source, string symbol, string name, string category, string frequency, string? unit, CancellationToken cancellationToken)
    {
        var existing = await dbContext.MarketSeries.FirstOrDefaultAsync(x => x.Symbol == symbol, cancellationToken);
        if (existing is not null)
        {
            return existing;
        }

        return dbContext.MarketSeries.Add(new MarketSeries
        {
            MacroDataSource = source,
            Symbol = symbol,
            Name = name,
            Category = category,
            Frequency = frequency,
            Unit = unit,
            IsProxy = true,
            IsHigherRiskOn = true
        }).Entity;
    }

    private async Task<DataVintage> EnsureDataVintageAsync(MacroSeries series, ImportBatch importBatch, DateOnly vintageDate, DateOnly realtimeStart, DateOnly realtimeEnd, string sourceSystem, string? sourceUrl, string? sourceHash, bool isOfficialVintage, CancellationToken cancellationToken)
    {
        var existing = await dbContext.DataVintages.FirstOrDefaultAsync(
            x => x.MacroSeriesId == series.Id && x.VintageDate == vintageDate && x.RealtimeStart == realtimeStart && x.RealtimeEnd == realtimeEnd,
            cancellationToken);

        if (existing is not null)
        {
            return existing;
        }

        return dbContext.DataVintages.Add(new DataVintage
        {
            MacroSeries = series,
            ImportBatch = importBatch,
            VintageDate = vintageDate,
            RealtimeStart = realtimeStart,
            RealtimeEnd = realtimeEnd,
            SourceSystem = sourceSystem,
            SourceUrl = sourceUrl,
            SourceHash = sourceHash,
            IsOfficialVintage = isOfficialVintage
        }).Entity;
    }

    private async Task UpsertMacroObservationAsync(MacroSeries series, DataVintage vintage, DateOnly observationDate, DateOnly publishedDate, decimal value, string vintageLabel, CancellationToken cancellationToken)
    {
        var existing = await dbContext.MacroObservations.FirstOrDefaultAsync(
            x => x.MacroSeriesId == series.Id && x.ObservationDate == observationDate && x.Vintage == vintageLabel,
            cancellationToken);

        if (existing is not null)
        {
            existing.Value = value;
            existing.PublishedDate = publishedDate;
            existing.DataVintage = vintage;
            existing.UpdatedAt = DateTimeOffset.UtcNow;
            return;
        }

        dbContext.MacroObservations.Add(new MacroObservation
        {
            MacroSeries = series,
            DataVintage = vintage,
            ObservationDate = observationDate,
            PublishedDate = publishedDate,
            Value = value,
            Vintage = vintageLabel,
            IsRevised = false
        });
    }

    private static string BuildFredObservationUrl(FredObservationImportRequest request)
    {
        var query = new Dictionary<string, string?>
        {
            ["series_id"] = request.SeriesCode,
            ["observation_start"] = request.ObservationStart.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["observation_end"] = request.ObservationEnd.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["realtime_start"] = request.RealtimeStart.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["realtime_end"] = request.RealtimeEnd.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
            ["file_type"] = "json",
            ["api_key"] = request.ApiKey
        };

        var encoded = query
            .Where(x => !string.IsNullOrWhiteSpace(x.Value))
            .Select(x => $"{Uri.EscapeDataString(x.Key)}={Uri.EscapeDataString(x.Value!)}");

        return "https://api.stlouisfed.org/fred/series/observations?" + string.Join("&", encoded);
    }

    private static List<string[]> ParseCsv(string csvContent)
    {
        return csvContent
            .Split(["\r\n", "\n"], StringSplitOptions.RemoveEmptyEntries)
            .Select(line => line.Split(',').Select(x => x.Trim().Trim('"')).ToArray())
            .ToList();
    }

    private static bool TryParseFredMdDate(string value, out DateOnly date)
    {
        return DateOnly.TryParseExact(value, "M/d/yyyy", CultureInfo.InvariantCulture, DateTimeStyles.None, out date)
            || DateOnly.TryParseExact(value, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out date)
            || DateOnly.TryParse(value, CultureInfo.InvariantCulture, DateTimeStyles.None, out date);
    }

    private static string Hash(string text)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(text));
        return Convert.ToHexString(bytes);
    }
}
