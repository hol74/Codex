using Finance.Application.Ledger;
using Finance.Domain.Entities;
using Finance.Domain.Enums;
using Finance.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace Finance.Infrastructure.Services;

public sealed class LedgerService(FinanceDbContext dbContext) : ILedgerService
{
    public async Task<IReadOnlyList<LedgerTransactionListItem>> GetTransactionsAsync(CancellationToken cancellationToken = default)
    {
        return await TransactionQuery()
            .OrderByDescending(x => x.TradeDate)
            .Select(x => new LedgerTransactionListItem(
                x.Id,
                x.TradeDate,
                x.Type.ToString(),
                x.Portfolio!.Name,
                x.Instrument != null ? x.Instrument.Symbol : null,
                x.Quantity,
                x.Price,
                x.GrossAmount,
                x.Fees,
                x.Taxes,
                x.PriceCurrency!.Code,
                x.CashAccount!.Name,
                x.SecuritiesAccount != null ? x.SecuritiesAccount.Name : null,
                x.Notes))
            .ToListAsync(cancellationToken);
    }

    public async Task<IReadOnlyList<LedgerTransactionListItem>> GetTransactionsAsync(TransactionType type, CancellationToken cancellationToken = default)
    {
        return await TransactionQuery()
            .Where(x => x.Type == type)
            .OrderByDescending(x => x.TradeDate)
            .Select(x => new LedgerTransactionListItem(
                x.Id,
                x.TradeDate,
                x.Type.ToString(),
                x.Portfolio!.Name,
                x.Instrument != null ? x.Instrument.Symbol : null,
                x.Quantity,
                x.Price,
                x.GrossAmount,
                x.Fees,
                x.Taxes,
                x.PriceCurrency!.Code,
                x.CashAccount!.Name,
                x.SecuritiesAccount != null ? x.SecuritiesAccount.Name : null,
                x.Notes))
            .ToListAsync(cancellationToken);
    }

    public async Task<TransactionFormPage> NewTransactionAsync(CancellationToken cancellationToken = default)
    {
        return await NewTransactionAsync(TransactionType.Buy, cancellationToken);
    }

    public async Task<TransactionFormPage> NewTransactionAsync(TransactionType type, CancellationToken cancellationToken = default)
    {
        var options = await GetOptionsAsync(cancellationToken);
        var model = new TransactionEditModel
        {
            TradeDate = DateTime.Today,
            SettlementDate = DateTime.Today,
            Type = type,
            PortfolioId = options.Portfolios.FirstOrDefault()?.Id ?? Guid.Empty,
            CashAccountId = options.CashAccounts.FirstOrDefault()?.Id ?? Guid.Empty,
            SecuritiesAccountId = type is TransactionType.Buy or TransactionType.Sell ? options.SecuritiesAccounts.FirstOrDefault()?.Id : null,
            InstrumentId = type is TransactionType.Buy or TransactionType.Sell ? options.Instruments.FirstOrDefault()?.Id : null,
            PriceCurrencyId = options.Currencies.FirstOrDefault(x => x.Label.StartsWith("EUR", StringComparison.OrdinalIgnoreCase))?.Id
                ?? options.Currencies.FirstOrDefault()?.Id
                ?? Guid.Empty,
            Price = 1m,
            FxRateToBase = 1m
        };

        return new TransactionFormPage(model, options);
    }

    public async Task<TransactionFormPage?> GetTransactionForEditAsync(Guid id, CancellationToken cancellationToken = default)
    {
        var transaction = await dbContext.Transactions.AsNoTracking().FirstOrDefaultAsync(x => x.Id == id, cancellationToken);
        if (transaction is null)
        {
            return null;
        }

        var options = await GetOptionsAsync(cancellationToken);
        var model = new TransactionEditModel
        {
            Id = transaction.Id,
            TradeDate = transaction.TradeDate.ToDateTime(TimeOnly.MinValue),
            SettlementDate = transaction.SettlementDate?.ToDateTime(TimeOnly.MinValue),
            Type = transaction.Type,
            PortfolioId = transaction.PortfolioId,
            InstrumentId = transaction.InstrumentId,
            CashAccountId = transaction.CashAccountId,
            SecuritiesAccountId = transaction.SecuritiesAccountId,
            Quantity = transaction.Quantity,
            Price = transaction.Price,
            PriceCurrencyId = transaction.PriceCurrencyId,
            GrossAmount = transaction.GrossAmount,
            Fees = transaction.Fees,
            Taxes = transaction.Taxes,
            FxRateToBase = transaction.FxRateToBase,
            Notes = transaction.Notes,
            ImportSource = transaction.ImportSource,
            BrokerTransactionId = transaction.BrokerTransactionId
        };

        return new TransactionFormPage(model, options);
    }

    public async Task<Guid> CreateTransactionAsync(TransactionEditModel model, CancellationToken cancellationToken = default)
    {
        Normalize(model);
        Validate(model);

        var transaction = new Transaction();
        ApplyModel(transaction, model);

        dbContext.Transactions.Add(transaction);
        AddAudit("TransactionCreated", $"Creata transazione {transaction.Type} del {transaction.TradeDate:yyyy-MM-dd}.");
        await dbContext.SaveChangesAsync(cancellationToken);

        return transaction.Id;
    }

    public async Task<bool> UpdateTransactionAsync(TransactionEditModel model, CancellationToken cancellationToken = default)
    {
        if (model.Id is null)
        {
            return false;
        }

        Normalize(model);
        Validate(model);

        var transaction = await dbContext.Transactions.FirstOrDefaultAsync(x => x.Id == model.Id.Value, cancellationToken);
        if (transaction is null)
        {
            return false;
        }

        ApplyModel(transaction, model);
        transaction.UpdatedAt = DateTimeOffset.UtcNow;
        AddAudit("TransactionUpdated", $"Aggiornata transazione {transaction.Type} del {transaction.TradeDate:yyyy-MM-dd}.");
        await dbContext.SaveChangesAsync(cancellationToken);

        return true;
    }

    public async Task<LedgerTransactionListItem?> GetTransactionForDeleteAsync(Guid id, CancellationToken cancellationToken = default)
    {
        return await TransactionQuery()
            .Where(x => x.Id == id)
            .Select(x => new LedgerTransactionListItem(
                x.Id,
                x.TradeDate,
                x.Type.ToString(),
                x.Portfolio!.Name,
                x.Instrument != null ? x.Instrument.Symbol : null,
                x.Quantity,
                x.Price,
                x.GrossAmount,
                x.Fees,
                x.Taxes,
                x.PriceCurrency!.Code,
                x.CashAccount!.Name,
                x.SecuritiesAccount != null ? x.SecuritiesAccount.Name : null,
                x.Notes))
            .FirstOrDefaultAsync(cancellationToken);
    }

    public async Task<bool> DeleteTransactionAsync(Guid id, CancellationToken cancellationToken = default)
    {
        var transaction = await dbContext.Transactions.FirstOrDefaultAsync(x => x.Id == id, cancellationToken);
        if (transaction is null)
        {
            return false;
        }

        dbContext.Transactions.Remove(transaction);
        AddAudit("TransactionDeleted", $"Eliminata transazione {transaction.Type} del {transaction.TradeDate:yyyy-MM-dd}.");
        await dbContext.SaveChangesAsync(cancellationToken);

        return true;
    }

    public async Task<CurrentPositionsSnapshot> GetCurrentPositionsAsync(CancellationToken cancellationToken = default)
    {
        var transactions = await dbContext.Transactions
            .AsNoTracking()
            .Include(x => x.Instrument)!.ThenInclude(x => x!.AssetClass)
            .Include(x => x.CashAccount)!.ThenInclude(x => x!.Currency)
            .OrderBy(x => x.TradeDate)
            .ToListAsync(cancellationToken);

        var instrumentPositions = transactions
            .Where(x => x.Instrument is not null && (x.Type == TransactionType.Buy || x.Type == TransactionType.Sell))
            .GroupBy(x => x.InstrumentId!.Value)
            .Select(group =>
            {
                var ordered = group.OrderBy(x => x.TradeDate).ToList();
                var last = ordered.Last();
                var quantity = ordered.Sum(x => x.Type == TransactionType.Buy ? x.Quantity : -x.Quantity);
                var costBasis = ordered
                    .Where(x => x.Type == TransactionType.Buy)
                    .Sum(x => ((x.Quantity * x.Price) + x.Fees + x.Taxes) * x.FxRateToBase);
                var lastPrice = last.Price;
                var marketValue = quantity * lastPrice * last.FxRateToBase;

                return new InstrumentPositionItem(
                    last.Instrument!.Symbol,
                    last.Instrument.Name,
                    last.Instrument.AssetClass?.Name ?? "-",
                    quantity,
                    lastPrice,
                    marketValue,
                    costBasis,
                    marketValue - costBasis);
            })
            .Where(x => x.Quantity != 0m)
            .OrderBy(x => x.AssetClass)
            .ThenBy(x => x.Symbol)
            .ToList();

        var cashBalances = transactions
            .GroupBy(x => x.CashAccountId)
            .Select(group =>
            {
                var last = group.First();
                var balance = group.Sum(GetCashDelta);

                return new CashBalanceItem(
                    last.CashAccount?.Name ?? "-",
                    last.CashAccount?.Currency?.Code ?? "-",
                    balance);
            })
            .OrderBy(x => x.AccountName)
            .ToList();

        return new CurrentPositionsSnapshot(
            instrumentPositions,
            cashBalances,
            instrumentPositions.Sum(x => x.MarketValueBase),
            cashBalances.Sum(x => x.Balance));
    }

    public async Task<IReadOnlyList<AuditEventListItem>> GetAuditEventsAsync(CancellationToken cancellationToken = default)
    {
        var events = await dbContext.AuditEvents.AsNoTracking().ToListAsync(cancellationToken);

        return events
            .OrderByDescending(x => x.CreatedAt)
            .Select(x => new AuditEventListItem(x.CreatedAt, x.Area, x.EventType, x.Message, x.Actor))
            .ToList();
    }

    public async Task<InstrumentFormPage> NewInstrumentAsync(CancellationToken cancellationToken = default)
    {
        var options = await GetInstrumentOptionsAsync(cancellationToken);
        var model = new InstrumentEditModel
        {
            Type = InstrumentType.Etf,
            CurrencyId = options.Currencies.FirstOrDefault(x => x.Label.StartsWith("EUR", StringComparison.OrdinalIgnoreCase))?.Id
                ?? options.Currencies.FirstOrDefault()?.Id
                ?? Guid.Empty,
            AssetClassId = options.AssetClasses.FirstOrDefault()?.Id ?? Guid.Empty
        };

        return new InstrumentFormPage(model, options);
    }

    public async Task<InstrumentFormPage?> GetInstrumentForEditAsync(Guid id, CancellationToken cancellationToken = default)
    {
        var instrument = await dbContext.Instruments.AsNoTracking().FirstOrDefaultAsync(x => x.Id == id, cancellationToken);
        if (instrument is null)
        {
            return null;
        }

        var model = new InstrumentEditModel
        {
            Id = instrument.Id,
            Name = instrument.Name,
            Symbol = instrument.Symbol,
            Isin = instrument.Isin,
            Exchange = instrument.Exchange,
            Type = instrument.Type,
            CurrencyId = instrument.CurrencyId,
            AssetClassId = instrument.AssetClassId
        };

        return new InstrumentFormPage(model, await GetInstrumentOptionsAsync(cancellationToken));
    }

    public async Task<Guid> CreateInstrumentAsync(InstrumentEditModel model, CancellationToken cancellationToken = default)
    {
        NormalizeInstrument(model);
        await ValidateInstrumentAsync(model, cancellationToken);

        var instrument = new Instrument
        {
            Name = model.Name,
            Symbol = model.Symbol
        };
        ApplyInstrumentModel(instrument, model);
        dbContext.Instruments.Add(instrument);
        AddAudit("InstrumentCreated", $"Creato strumento {instrument.Symbol}.");
        await dbContext.SaveChangesAsync(cancellationToken);

        return instrument.Id;
    }

    public async Task<bool> UpdateInstrumentAsync(InstrumentEditModel model, CancellationToken cancellationToken = default)
    {
        if (model.Id is null)
        {
            return false;
        }

        NormalizeInstrument(model);
        await ValidateInstrumentAsync(model, cancellationToken);

        var instrument = await dbContext.Instruments.FirstOrDefaultAsync(x => x.Id == model.Id.Value, cancellationToken);
        if (instrument is null)
        {
            return false;
        }

        ApplyInstrumentModel(instrument, model);
        instrument.UpdatedAt = DateTimeOffset.UtcNow;
        AddAudit("InstrumentUpdated", $"Aggiornato strumento {instrument.Symbol}.");
        await dbContext.SaveChangesAsync(cancellationToken);

        return true;
    }

    public async Task<InstrumentEditModel?> GetInstrumentForDeleteAsync(Guid id, CancellationToken cancellationToken = default)
    {
        return await dbContext.Instruments
            .AsNoTracking()
            .Where(x => x.Id == id)
            .Select(x => new InstrumentEditModel
            {
                Id = x.Id,
                Name = x.Name,
                Symbol = x.Symbol,
                Isin = x.Isin,
                Exchange = x.Exchange,
                Type = x.Type,
                CurrencyId = x.CurrencyId,
                AssetClassId = x.AssetClassId
            })
            .FirstOrDefaultAsync(cancellationToken);
    }

    public async Task<bool> DeleteInstrumentAsync(Guid id, CancellationToken cancellationToken = default)
    {
        var instrument = await dbContext.Instruments.FirstOrDefaultAsync(x => x.Id == id, cancellationToken);
        if (instrument is null)
        {
            return false;
        }

        var isUsed = await dbContext.Transactions.AnyAsync(x => x.InstrumentId == id, cancellationToken)
            || await dbContext.Prices.AnyAsync(x => x.InstrumentId == id, cancellationToken)
            || await dbContext.CorporateActions.AnyAsync(x => x.InstrumentId == id, cancellationToken);

        if (isUsed)
        {
            throw new InvalidOperationException("Lo strumento non puo' essere eliminato perche' e' gia' usato da transazioni, prezzi o corporate action.");
        }

        dbContext.Instruments.Remove(instrument);
        AddAudit("InstrumentDeleted", $"Eliminato strumento {instrument.Symbol}.");
        await dbContext.SaveChangesAsync(cancellationToken);

        return true;
    }

    private IQueryable<Transaction> TransactionQuery()
    {
        return dbContext.Transactions
            .AsNoTracking()
            .Include(x => x.Portfolio)
            .Include(x => x.Instrument)
            .Include(x => x.PriceCurrency)
            .Include(x => x.CashAccount)
            .Include(x => x.SecuritiesAccount);
    }

    private async Task<TransactionFormOptions> GetOptionsAsync(CancellationToken cancellationToken)
    {
        var portfolios = await dbContext.Portfolios
            .AsNoTracking()
            .OrderBy(x => x.Name)
            .Select(x => new LookupItem(x.Id, x.Name))
            .ToListAsync(cancellationToken);

        var cashAccounts = await dbContext.Accounts
            .AsNoTracking()
            .Include(x => x.Currency)
            .Where(x => x.Type == AccountType.Cash || x.Type == AccountType.MultiAsset)
            .OrderBy(x => x.Name)
            .Select(x => new LookupItem(x.Id, x.Name + " (" + x.Currency!.Code + ")"))
            .ToListAsync(cancellationToken);

        var securitiesAccounts = await dbContext.Accounts
            .AsNoTracking()
            .Where(x => x.Type == AccountType.Securities || x.Type == AccountType.MultiAsset)
            .OrderBy(x => x.Name)
            .Select(x => new LookupItem(x.Id, x.Name))
            .ToListAsync(cancellationToken);

        var instruments = await dbContext.Instruments
            .AsNoTracking()
            .OrderBy(x => x.Symbol)
            .Select(x => new LookupItem(x.Id, x.Symbol + " - " + x.Name))
            .ToListAsync(cancellationToken);

        var currencies = await dbContext.Currencies
            .AsNoTracking()
            .OrderBy(x => x.Code)
            .Select(x => new LookupItem(x.Id, x.Code + " - " + x.Name))
            .ToListAsync(cancellationToken);

        var transactionTypes = new[]
        {
            new TransactionTypeItem(TransactionType.Buy, "Acquisto"),
            new TransactionTypeItem(TransactionType.Sell, "Vendita"),
            new TransactionTypeItem(TransactionType.Deposit, "Deposito"),
            new TransactionTypeItem(TransactionType.Withdrawal, "Prelievo")
        };

        return new TransactionFormOptions(portfolios, cashAccounts, securitiesAccounts, instruments, currencies, transactionTypes);
    }

    private async Task<InstrumentFormOptions> GetInstrumentOptionsAsync(CancellationToken cancellationToken)
    {
        var currencies = await dbContext.Currencies
            .AsNoTracking()
            .OrderBy(x => x.Code)
            .Select(x => new LookupItem(x.Id, x.Code + " - " + x.Name))
            .ToListAsync(cancellationToken);

        var assetClasses = await dbContext.AssetClasses
            .AsNoTracking()
            .OrderBy(x => x.Name)
            .Select(x => new LookupItem(x.Id, x.Name))
            .ToListAsync(cancellationToken);

        var instrumentTypes = Enum.GetValues<InstrumentType>()
            .Select(x => new InstrumentTypeItem(x, x.ToString()))
            .ToList();

        return new InstrumentFormOptions(currencies, assetClasses, instrumentTypes);
    }

    private static void Normalize(TransactionEditModel model)
    {
        model.Fees = Math.Abs(model.Fees);
        model.Taxes = Math.Abs(model.Taxes);

        if (model.Type is TransactionType.Deposit or TransactionType.Withdrawal)
        {
            model.Quantity = 0m;
            model.Price = model.Price <= 0m ? 1m : model.Price;
            model.InstrumentId = null;
            model.SecuritiesAccountId = null;
        }

        if (model.Type == TransactionType.Deposit)
        {
            model.GrossAmount = Math.Abs(model.GrossAmount);
        }
        else if (model.Type == TransactionType.Withdrawal)
        {
            model.GrossAmount = -Math.Abs(model.GrossAmount);
        }
        else if (model.Type == TransactionType.Buy)
        {
            var notional = model.GrossAmount == 0m ? model.Quantity * model.Price : Math.Abs(model.GrossAmount);
            model.GrossAmount = -notional;
        }
        else if (model.Type == TransactionType.Sell)
        {
            var notional = model.GrossAmount == 0m ? model.Quantity * model.Price : Math.Abs(model.GrossAmount);
            model.GrossAmount = notional;
        }
    }

    private static void Validate(TransactionEditModel model)
    {
        if (model.PortfolioId == Guid.Empty || model.CashAccountId == Guid.Empty || model.PriceCurrencyId == Guid.Empty)
        {
            throw new InvalidOperationException("Portafoglio, conto cash e valuta sono obbligatori.");
        }

        if (model.Type is TransactionType.Buy or TransactionType.Sell)
        {
            if (model.InstrumentId is null || model.SecuritiesAccountId is null)
            {
                throw new InvalidOperationException("Acquisti e vendite richiedono strumento e conto titoli.");
            }

            if (model.Quantity <= 0m || model.Price <= 0m)
            {
                throw new InvalidOperationException("Acquisti e vendite richiedono quantita e prezzo maggiori di zero.");
            }
        }

        if (model.Type is TransactionType.Deposit or TransactionType.Withdrawal && model.GrossAmount == 0m)
        {
            throw new InvalidOperationException("Depositi e prelievi richiedono un importo diverso da zero.");
        }
    }

    private async Task ValidateInstrumentAsync(InstrumentEditModel model, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(model.Symbol) || string.IsNullOrWhiteSpace(model.Name))
        {
            throw new InvalidOperationException("Simbolo e nome sono obbligatori.");
        }

        if (model.CurrencyId == Guid.Empty || model.AssetClassId == Guid.Empty)
        {
            throw new InvalidOperationException("Valuta e asset class sono obbligatorie.");
        }

        var modelId = model.Id ?? Guid.Empty;
        var duplicate = await dbContext.Instruments.AnyAsync(
            x => x.Id != modelId
                && x.Symbol == model.Symbol
                && x.Exchange == model.Exchange,
            cancellationToken);

        if (duplicate)
        {
            throw new InvalidOperationException("Esiste gia' uno strumento con lo stesso simbolo ed exchange.");
        }
    }

    private static void ApplyModel(Transaction transaction, TransactionEditModel model)
    {
        transaction.TradeDate = DateOnly.FromDateTime(model.TradeDate);
        transaction.SettlementDate = model.SettlementDate.HasValue ? DateOnly.FromDateTime(model.SettlementDate.Value) : null;
        transaction.Type = model.Type;
        transaction.PortfolioId = model.PortfolioId;
        transaction.InstrumentId = model.InstrumentId;
        transaction.CashAccountId = model.CashAccountId;
        transaction.SecuritiesAccountId = model.SecuritiesAccountId;
        transaction.Quantity = model.Quantity;
        transaction.Price = model.Price;
        transaction.PriceCurrencyId = model.PriceCurrencyId;
        transaction.GrossAmount = model.GrossAmount;
        transaction.Fees = model.Fees;
        transaction.Taxes = model.Taxes;
        transaction.FxRateToBase = model.FxRateToBase;
        transaction.Notes = model.Notes;
        transaction.ImportSource = string.IsNullOrWhiteSpace(model.ImportSource) ? "Manual" : model.ImportSource;
        transaction.BrokerTransactionId = model.BrokerTransactionId;
    }

    private static void NormalizeInstrument(InstrumentEditModel model)
    {
        model.Symbol = model.Symbol.Trim().ToUpperInvariant();
        model.Name = model.Name.Trim();
        model.Isin = string.IsNullOrWhiteSpace(model.Isin) ? null : model.Isin.Trim().ToUpperInvariant();
        model.Exchange = string.IsNullOrWhiteSpace(model.Exchange) ? null : model.Exchange.Trim().ToUpperInvariant();
    }

    private static void ApplyInstrumentModel(Instrument instrument, InstrumentEditModel model)
    {
        instrument.Name = model.Name;
        instrument.Symbol = model.Symbol;
        instrument.Isin = model.Isin;
        instrument.Exchange = model.Exchange;
        instrument.Type = model.Type;
        instrument.CurrencyId = model.CurrencyId;
        instrument.AssetClassId = model.AssetClassId;
    }

    private static decimal GetCashDelta(Transaction transaction)
    {
        return transaction.GrossAmount - transaction.Fees - transaction.Taxes;
    }

    private void AddAudit(string eventType, string message)
    {
        dbContext.AuditEvents.Add(new AuditEvent
        {
            Area = "Ledger",
            EventType = eventType,
            Message = message,
            Actor = "system"
        });
    }
}
