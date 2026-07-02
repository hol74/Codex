using Finance.Application.Ledger;
using Microsoft.AspNetCore.Mvc;

namespace Finance.Web.Controllers;

public class PositionsController(ILedgerService ledgerService) : Controller
{
    public async Task<IActionResult> Index(CancellationToken cancellationToken)
    {
        var positions = await ledgerService.GetCurrentPositionsAsync(cancellationToken);
        return View(positions);
    }
}
