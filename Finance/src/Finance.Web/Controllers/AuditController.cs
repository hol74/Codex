using Finance.Application.Ledger;
using Microsoft.AspNetCore.Mvc;

namespace Finance.Web.Controllers;

public class AuditController(ILedgerService ledgerService) : Controller
{
    public async Task<IActionResult> Index(CancellationToken cancellationToken)
    {
        var events = await ledgerService.GetAuditEventsAsync(cancellationToken);
        return View(events);
    }
}
