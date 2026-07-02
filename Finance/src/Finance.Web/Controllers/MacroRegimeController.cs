using Finance.Application.MacroRegime;
using Microsoft.AspNetCore.Mvc;

namespace Finance.Web.Controllers;

public sealed class MacroRegimeController(
    IMacroRegimeService macroRegimeService,
    IRegimeCalculationService regimeCalculationService) : Controller
{
    public async Task<IActionResult> Index(CancellationToken cancellationToken)
    {
        var dashboard = await macroRegimeService.GetDashboardAsync(cancellationToken);
        if (dashboard is null)
        {
            return View("Empty");
        }

        return View(dashboard);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Calculate(DateOnly asOfDate, CancellationToken cancellationToken)
    {
        var result = await regimeCalculationService.CalculateAsync(asOfDate, cancellationToken: cancellationToken);
        TempData["MacroRegimeMessage"] = $"Calcolo completato as-of {result.AsOfDate:yyyy-MM-dd}: {result.PrimaryRegime}, confidence {result.Confidence:P0}.";

        if (result.Warnings.Count > 0)
        {
            TempData["MacroRegimeWarning"] = string.Join(" ", result.Warnings);
        }

        return RedirectToAction(nameof(Index));
    }
}
