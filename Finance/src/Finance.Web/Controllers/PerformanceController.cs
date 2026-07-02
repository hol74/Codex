using Finance.Application.Performance;
using Microsoft.AspNetCore.Mvc;

namespace Finance.Web.Controllers;

public sealed class PerformanceController(IPerformanceService performanceService) : Controller
{
    public async Task<IActionResult> Index(CancellationToken cancellationToken)
    {
        var dashboard = await performanceService.GetDashboardAsync(cancellationToken);
        if (dashboard is null)
        {
            return View("Empty");
        }

        return View(dashboard);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Rebuild(CancellationToken cancellationToken)
    {
        await performanceService.RebuildSnapshotsAsync(cancellationToken);
        return RedirectToAction(nameof(Index));
    }
}
