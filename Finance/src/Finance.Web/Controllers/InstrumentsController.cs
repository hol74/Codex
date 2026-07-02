using Finance.Application.PhaseOne;
using Finance.Application.Ledger;
using Microsoft.AspNetCore.Mvc;

namespace Finance.Web.Controllers;

public class InstrumentsController(IPhaseOneReadService readService, ILedgerService ledgerService) : Controller
{
    public async Task<IActionResult> Index(CancellationToken cancellationToken)
    {
        var instruments = await readService.GetInstrumentsAsync(cancellationToken);
        return View(instruments);
    }

    public async Task<IActionResult> Create(CancellationToken cancellationToken)
    {
        var page = await ledgerService.NewInstrumentAsync(cancellationToken);
        return View(page);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create([Bind(Prefix = "Instrument")] InstrumentEditModel instrument, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return View(await RebuildFormAsync(instrument, cancellationToken));
        }

        try
        {
            await ledgerService.CreateInstrumentAsync(instrument, cancellationToken);
            return RedirectToAction(nameof(Index));
        }
        catch (InvalidOperationException ex)
        {
            ModelState.AddModelError(string.Empty, ex.Message);
            return View(await RebuildFormAsync(instrument, cancellationToken));
        }
    }

    public async Task<IActionResult> Edit(Guid id, CancellationToken cancellationToken)
    {
        var page = await ledgerService.GetInstrumentForEditAsync(id, cancellationToken);
        return page is null ? NotFound() : View(page);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(Guid id, [Bind(Prefix = "Instrument")] InstrumentEditModel instrument, CancellationToken cancellationToken)
    {
        instrument.Id = id;

        if (!ModelState.IsValid)
        {
            return View(await RebuildFormAsync(instrument, cancellationToken));
        }

        try
        {
            var updated = await ledgerService.UpdateInstrumentAsync(instrument, cancellationToken);
            return updated ? RedirectToAction(nameof(Index)) : NotFound();
        }
        catch (InvalidOperationException ex)
        {
            ModelState.AddModelError(string.Empty, ex.Message);
            return View(await RebuildFormAsync(instrument, cancellationToken));
        }
    }

    public async Task<IActionResult> Delete(Guid id, CancellationToken cancellationToken)
    {
        var instrument = await ledgerService.GetInstrumentForDeleteAsync(id, cancellationToken);
        return instrument is null ? NotFound() : View(instrument);
    }

    [HttpPost, ActionName("Delete")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> DeleteConfirmed(Guid id, CancellationToken cancellationToken)
    {
        try
        {
            var deleted = await ledgerService.DeleteInstrumentAsync(id, cancellationToken);
            return deleted ? RedirectToAction(nameof(Index)) : NotFound();
        }
        catch (InvalidOperationException ex)
        {
            var instrument = await ledgerService.GetInstrumentForDeleteAsync(id, cancellationToken);
            if (instrument is null)
            {
                return NotFound();
            }

            ModelState.AddModelError(string.Empty, ex.Message);
            return View(instrument);
        }
    }

    private async Task<InstrumentFormPage> RebuildFormAsync(InstrumentEditModel instrument, CancellationToken cancellationToken)
    {
        var defaults = await ledgerService.NewInstrumentAsync(cancellationToken);
        return new InstrumentFormPage(instrument, defaults.Options);
    }
}
