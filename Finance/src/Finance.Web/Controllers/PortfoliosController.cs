using Finance.Application.PhaseOne;
using Microsoft.AspNetCore.Mvc;

namespace Finance.Web.Controllers;

public class PortfoliosController(IPhaseOneReadService readService) : Controller
{
    public async Task<IActionResult> Index(CancellationToken cancellationToken)
    {
        var portfolios = await readService.GetPortfoliosAsync(cancellationToken);
        return View(portfolios);
    }
}
