using Finance.Application.MacroRegime;
using Microsoft.AspNetCore.Mvc;

namespace Finance.Web.Controllers;

public sealed class MacroDataController(IMacroDataFoundationService macroDataFoundationService) : Controller
{
    public async Task<IActionResult> Index(DateOnly? asOfDate, CancellationToken cancellationToken)
    {
        var dashboard = await macroDataFoundationService.GetDashboardAsync(asOfDate, cancellationToken);
        return View(dashboard);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> ImportFred(FredImportForm form, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(form.SeriesCode))
        {
            TempData["MacroDataMessage"] = "Indica il codice serie FRED.";
            return RedirectToAction(nameof(Index));
        }

        var result = await macroDataFoundationService.ImportFredObservationsAsync(new FredObservationImportRequest(
            form.SeriesCode.Trim(),
            form.ObservationStart,
            form.ObservationEnd,
            form.RealtimeStart,
            form.RealtimeEnd,
            form.ApiKey),
            cancellationToken);

        TempData["MacroDataMessage"] = FormatImportResult(result);
        return RedirectToAction(nameof(Index), new { asOfDate = form.RealtimeEnd.ToString("yyyy-MM-dd") });
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> ImportFredMd(FredMdImportForm form, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(form.CsvContent))
        {
            TempData["MacroDataMessage"] = "Incolla il contenuto CSV FRED-MD.";
            return RedirectToAction(nameof(Index));
        }

        var mapping = ParseMapping(form.ColumnMapping);
        if (mapping.Count == 0)
        {
            TempData["MacroDataMessage"] = "Indica almeno una mappatura COLUMN=SERIES_CODE.";
            return RedirectToAction(nameof(Index));
        }

        var result = await macroDataFoundationService.ImportFredMdCsvAsync(new FredMdCsvImportRequest(
            form.CsvContent,
            form.VintageDate,
            form.PublishedDate,
            mapping),
            cancellationToken);

        TempData["MacroDataMessage"] = FormatImportResult(result);
        return RedirectToAction(nameof(Index), new { asOfDate = form.PublishedDate.ToString("yyyy-MM-dd") });
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> ImportMarket(MarketImportForm form, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(form.Symbol))
        {
            TempData["MacroDataMessage"] = "Indica il simbolo della serie di mercato.";
            return RedirectToAction(nameof(Index));
        }

        var result = await macroDataFoundationService.ImportMarketObservationsAsync(new MarketObservationImportRequest(
            form.Symbol.Trim(),
            [new MarketObservationInput(form.Date, form.Value, form.AvailableDate, form.SourceHash, form.Notes)],
            string.IsNullOrWhiteSpace(form.SourceSystem) ? "ManualMarketData" : form.SourceSystem.Trim()),
            cancellationToken);

        TempData["MacroDataMessage"] = FormatImportResult(result);
        return RedirectToAction(nameof(Index), new { asOfDate = form.AvailableDate.ToString("yyyy-MM-dd") });
    }

    private static Dictionary<string, string> ParseMapping(string? mapping)
    {
        return (mapping ?? string.Empty)
            .Split(["\r\n", "\n"], StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Select(line => line.Split('=', 2, StringSplitOptions.TrimEntries))
            .Where(parts => parts.Length == 2 && !string.IsNullOrWhiteSpace(parts[0]) && !string.IsNullOrWhiteSpace(parts[1]))
            .ToDictionary(parts => parts[0], parts => parts[1], StringComparer.OrdinalIgnoreCase);
    }

    private static string FormatImportResult(MacroDataImportResult result)
    {
        return $"{result.Source}: letti {result.RecordsRead}, accettati {result.RecordsAccepted}, scartati {result.RecordsRejected}. {string.Join(" ", result.Messages)}";
    }
}

public sealed class FredImportForm
{
    public string SeriesCode { get; set; } = "T10YIE";
    public DateOnly ObservationStart { get; set; } = DateOnly.FromDateTime(DateTime.Today.AddMonths(-3));
    public DateOnly ObservationEnd { get; set; } = DateOnly.FromDateTime(DateTime.Today);
    public DateOnly RealtimeStart { get; set; } = DateOnly.FromDateTime(DateTime.Today);
    public DateOnly RealtimeEnd { get; set; } = DateOnly.FromDateTime(DateTime.Today);
    public string? ApiKey { get; set; }
}

public sealed class FredMdImportForm
{
    public DateOnly VintageDate { get; set; } = DateOnly.FromDateTime(DateTime.Today);
    public DateOnly PublishedDate { get; set; } = DateOnly.FromDateTime(DateTime.Today);
    public string ColumnMapping { get; set; } = "INDPRO=FREDMD_INDPRO";
    public string CsvContent { get; set; } = string.Empty;
}

public sealed class MarketImportForm
{
    public string Symbol { get; set; } = "VWCE_PROXY";
    public DateOnly Date { get; set; } = DateOnly.FromDateTime(DateTime.Today);
    public decimal Value { get; set; }
    public DateOnly AvailableDate { get; set; } = DateOnly.FromDateTime(DateTime.Today);
    public string SourceSystem { get; set; } = "ManualMarketData";
    public string? SourceHash { get; set; }
    public string? Notes { get; set; }
}
