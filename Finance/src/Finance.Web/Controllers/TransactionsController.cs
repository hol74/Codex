using Finance.Application.Ledger;
using Finance.Domain.Enums;
using Microsoft.AspNetCore.Mvc;

namespace Finance.Web.Controllers;

public class TransactionsController(ILedgerService ledgerService) : Controller
{
    public async Task<IActionResult> Index(CancellationToken cancellationToken)
    {
        ViewData["Title"] = "Transazioni";
        ViewData["TransactionHeading"] = "Transazioni";
        ViewData["TransactionEyebrow"] = "Ledger";
        var transactions = await ledgerService.GetTransactionsAsync(cancellationToken);
        return View(transactions);
    }

    public async Task<IActionResult> Deposits(CancellationToken cancellationToken)
    {
        return await TransactionListAsync(TransactionType.Deposit, "Depositi", "Movimenti cash", cancellationToken);
    }

    public async Task<IActionResult> Withdrawals(CancellationToken cancellationToken)
    {
        return await TransactionListAsync(TransactionType.Withdrawal, "Prelievi", "Movimenti cash", cancellationToken);
    }

    public async Task<IActionResult> Buys(CancellationToken cancellationToken)
    {
        return await TransactionListAsync(TransactionType.Buy, "Acquisti", "Operazioni titoli", cancellationToken);
    }

    public async Task<IActionResult> Sells(CancellationToken cancellationToken)
    {
        return await TransactionListAsync(TransactionType.Sell, "Vendite", "Operazioni titoli", cancellationToken);
    }

    public async Task<IActionResult> Create(CancellationToken cancellationToken)
    {
        ViewData["Title"] = "Nuova transazione";
        ViewData["TransactionHeading"] = "Nuova transazione";
        ViewData["FormAction"] = nameof(Create);
        ViewData["CancelAction"] = nameof(Index);
        var page = await ledgerService.NewTransactionAsync(cancellationToken);
        return View(page);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Create([Bind(Prefix = "Transaction")] TransactionEditModel transaction, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return View(await RebuildFormAsync(transaction, cancellationToken));
        }

        try
        {
            await ledgerService.CreateTransactionAsync(transaction, cancellationToken);
            return RedirectToAction(nameof(Index));
        }
        catch (InvalidOperationException ex)
        {
            ModelState.AddModelError(string.Empty, ex.Message);
            return View(await RebuildFormAsync(transaction, cancellationToken));
        }
    }

    public async Task<IActionResult> CreateDeposit(CancellationToken cancellationToken)
    {
        return await CreateTypedAsync(TransactionType.Deposit, "Nuovo deposito", cancellationToken);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> CreateDeposit([Bind(Prefix = "Transaction")] TransactionEditModel transaction, CancellationToken cancellationToken)
    {
        return await CreateTypedAsync(transaction, TransactionType.Deposit, nameof(Deposits), "Nuovo deposito", cancellationToken);
    }

    public async Task<IActionResult> CreateWithdrawal(CancellationToken cancellationToken)
    {
        return await CreateTypedAsync(TransactionType.Withdrawal, "Nuovo prelievo", cancellationToken);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> CreateWithdrawal([Bind(Prefix = "Transaction")] TransactionEditModel transaction, CancellationToken cancellationToken)
    {
        return await CreateTypedAsync(transaction, TransactionType.Withdrawal, nameof(Withdrawals), "Nuovo prelievo", cancellationToken);
    }

    public async Task<IActionResult> CreateBuy(CancellationToken cancellationToken)
    {
        return await CreateTypedAsync(TransactionType.Buy, "Nuovo acquisto", cancellationToken);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> CreateBuy([Bind(Prefix = "Transaction")] TransactionEditModel transaction, CancellationToken cancellationToken)
    {
        return await CreateTypedAsync(transaction, TransactionType.Buy, nameof(Buys), "Nuovo acquisto", cancellationToken);
    }

    public async Task<IActionResult> CreateSell(CancellationToken cancellationToken)
    {
        return await CreateTypedAsync(TransactionType.Sell, "Nuova vendita", cancellationToken);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> CreateSell([Bind(Prefix = "Transaction")] TransactionEditModel transaction, CancellationToken cancellationToken)
    {
        return await CreateTypedAsync(transaction, TransactionType.Sell, nameof(Sells), "Nuova vendita", cancellationToken);
    }

    public async Task<IActionResult> Edit(Guid id, CancellationToken cancellationToken)
    {
        var page = await ledgerService.GetTransactionForEditAsync(id, cancellationToken);
        return page is null ? NotFound() : View(page);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(Guid id, [Bind(Prefix = "Transaction")] TransactionEditModel transaction, CancellationToken cancellationToken)
    {
        transaction.Id = id;

        if (!ModelState.IsValid)
        {
            return View(await RebuildFormAsync(transaction, cancellationToken));
        }

        try
        {
            var updated = await ledgerService.UpdateTransactionAsync(transaction, cancellationToken);
            return updated ? RedirectToAction(nameof(Index)) : NotFound();
        }
        catch (InvalidOperationException ex)
        {
            ModelState.AddModelError(string.Empty, ex.Message);
            return View(await RebuildFormAsync(transaction, cancellationToken));
        }
    }

    public async Task<IActionResult> Delete(Guid id, CancellationToken cancellationToken)
    {
        var transaction = await ledgerService.GetTransactionForDeleteAsync(id, cancellationToken);
        return transaction is null ? NotFound() : View(transaction);
    }

    [HttpPost, ActionName("Delete")]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> DeleteConfirmed(Guid id, CancellationToken cancellationToken)
    {
        var deleted = await ledgerService.DeleteTransactionAsync(id, cancellationToken);
        return deleted ? RedirectToAction(nameof(Index)) : NotFound();
    }

    private async Task<TransactionFormPage> RebuildFormAsync(TransactionEditModel transaction, CancellationToken cancellationToken)
    {
        var defaults = await ledgerService.NewTransactionAsync(transaction.Type, cancellationToken);
        return new TransactionFormPage(transaction, defaults.Options);
    }

    private async Task<IActionResult> TransactionListAsync(TransactionType type, string heading, string eyebrow, CancellationToken cancellationToken)
    {
        ViewData["Title"] = heading;
        ViewData["TransactionHeading"] = heading;
        ViewData["TransactionEyebrow"] = eyebrow;
        ViewData["CreateAction"] = type switch
        {
            TransactionType.Deposit => nameof(CreateDeposit),
            TransactionType.Withdrawal => nameof(CreateWithdrawal),
            TransactionType.Buy => nameof(CreateBuy),
            TransactionType.Sell => nameof(CreateSell),
            _ => nameof(Create)
        };

        var transactions = await ledgerService.GetTransactionsAsync(type, cancellationToken);
        return View("Index", transactions);
    }

    private async Task<IActionResult> CreateTypedAsync(TransactionType type, string heading, CancellationToken cancellationToken)
    {
        ViewData["Title"] = heading;
        ViewData["TransactionHeading"] = heading;
        ViewData["FixedTransactionType"] = type;
        ViewData["FormAction"] = type switch
        {
            TransactionType.Deposit => nameof(CreateDeposit),
            TransactionType.Withdrawal => nameof(CreateWithdrawal),
            TransactionType.Buy => nameof(CreateBuy),
            TransactionType.Sell => nameof(CreateSell),
            _ => nameof(Create)
        };
        ViewData["CancelAction"] = type switch
        {
            TransactionType.Deposit => nameof(Deposits),
            TransactionType.Withdrawal => nameof(Withdrawals),
            TransactionType.Buy => nameof(Buys),
            TransactionType.Sell => nameof(Sells),
            _ => nameof(Index)
        };
        var page = await ledgerService.NewTransactionAsync(type, cancellationToken);
        return View("Create", page);
    }

    private async Task<IActionResult> CreateTypedAsync(
        TransactionEditModel transaction,
        TransactionType type,
        string redirectAction,
        string heading,
        CancellationToken cancellationToken)
    {
        transaction.Type = type;
        ViewData["Title"] = heading;
        ViewData["TransactionHeading"] = heading;
        ViewData["FixedTransactionType"] = type;
        ViewData["FormAction"] = type switch
        {
            TransactionType.Deposit => nameof(CreateDeposit),
            TransactionType.Withdrawal => nameof(CreateWithdrawal),
            TransactionType.Buy => nameof(CreateBuy),
            TransactionType.Sell => nameof(CreateSell),
            _ => nameof(Create)
        };
        ViewData["CancelAction"] = redirectAction;

        if (!ModelState.IsValid)
        {
            return View("Create", await RebuildFormAsync(transaction, cancellationToken));
        }

        try
        {
            await ledgerService.CreateTransactionAsync(transaction, cancellationToken);
            return RedirectToAction(redirectAction);
        }
        catch (InvalidOperationException ex)
        {
            ModelState.AddModelError(string.Empty, ex.Message);
            return View("Create", await RebuildFormAsync(transaction, cancellationToken));
        }
    }
}
