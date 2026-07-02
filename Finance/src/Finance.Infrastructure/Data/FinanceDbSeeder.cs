using Finance.Domain.Entities;
using Finance.Domain.Enums;
using Microsoft.EntityFrameworkCore;

namespace Finance.Infrastructure.Data;

public static class FinanceDbSeeder
{
    public static async Task EnsurePhaseSixSchemaAsync(FinanceDbContext dbContext, CancellationToken cancellationToken = default)
    {
        var statements = new[]
        {
            """
            CREATE TABLE IF NOT EXISTS "MacroDataSources" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_MacroDataSources" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "Name" TEXT NOT NULL,
                "Kind" TEXT NOT NULL,
                "Url" TEXT NULL,
                "ApiBaseUrl" TEXT NULL,
                "SupportsVintageData" INTEGER NOT NULL DEFAULT 0,
                "Notes" TEXT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "MacroSeries" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_MacroSeries" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "MacroDataSourceId" TEXT NOT NULL,
                "Code" TEXT NOT NULL,
                "Name" TEXT NOT NULL,
                "Category" TEXT NOT NULL,
                "Frequency" TEXT NOT NULL,
                "Unit" TEXT NULL,
                "IsHigherRiskOn" INTEGER NOT NULL,
                "PublicationLagDays" INTEGER NOT NULL,
                "FredSeriesId" TEXT NULL,
                "FredMdColumn" TEXT NULL,
                "RequiresVintageTracking" INTEGER NOT NULL DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "DataVintages" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_DataVintages" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "MacroSeriesId" TEXT NOT NULL,
                "ImportBatchId" TEXT NULL,
                "VintageDate" TEXT NOT NULL,
                "RealtimeStart" TEXT NOT NULL,
                "RealtimeEnd" TEXT NOT NULL,
                "RetrievedAt" TEXT NOT NULL,
                "SourceSystem" TEXT NOT NULL,
                "SourceUrl" TEXT NULL,
                "SourceHash" TEXT NULL,
                "IsOfficialVintage" INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "MacroObservations" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_MacroObservations" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "MacroSeriesId" TEXT NOT NULL,
                "DataVintageId" TEXT NULL,
                "ObservationDate" TEXT NOT NULL,
                "PublishedDate" TEXT NOT NULL,
                "Value" TEXT NOT NULL,
                "Vintage" TEXT NULL,
                "IsRevised" INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "ReleaseCalendar" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_ReleaseCalendar" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "MacroDataSourceId" TEXT NOT NULL,
                "ReleaseCode" TEXT NOT NULL,
                "Name" TEXT NOT NULL,
                "ReleaseDate" TEXT NOT NULL,
                "ObservationPeriodStart" TEXT NULL,
                "ObservationPeriodEnd" TEXT NULL,
                "Frequency" TEXT NOT NULL,
                "SourceUrl" TEXT NULL,
                "Status" TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "MarketSeries" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_MarketSeries" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "MacroDataSourceId" TEXT NOT NULL,
                "Symbol" TEXT NOT NULL,
                "Name" TEXT NOT NULL,
                "Category" TEXT NOT NULL,
                "Frequency" TEXT NOT NULL,
                "Unit" TEXT NULL,
                "CurrencyCode" TEXT NULL,
                "AssetClassCode" TEXT NULL,
                "ProxyRole" TEXT NULL,
                "IsProxy" INTEGER NOT NULL,
                "IsHigherRiskOn" INTEGER NOT NULL,
                "InstrumentId" TEXT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "MarketObservations" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_MarketObservations" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "MarketSeriesId" TEXT NOT NULL,
                "Date" TEXT NOT NULL,
                "Value" TEXT NOT NULL,
                "AvailableDate" TEXT NOT NULL,
                "SourceHash" TEXT NULL,
                "Notes" TEXT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "MacroFeatureSetVersions" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_MacroFeatureSetVersions" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "Name" TEXT NOT NULL,
                "Version" TEXT NOT NULL,
                "Description" TEXT NULL,
                "IsActive" INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "MacroFeatureDefinitions" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_MacroFeatureDefinitions" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "MacroFeatureSetVersionId" TEXT NOT NULL,
                "Code" TEXT NOT NULL,
                "Name" TEXT NOT NULL,
                "Dimension" TEXT NOT NULL,
                "Formula" TEXT NOT NULL,
                "Weight" TEXT NOT NULL,
                "LookbackMonths" INTEGER NOT NULL,
                "IsHigherRiskOn" INTEGER NOT NULL,
                "IsActive" INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "MacroFeatureValues" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_MacroFeatureValues" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "MacroFeatureDefinitionId" TEXT NOT NULL,
                "MacroObservationId" TEXT NULL,
                "MarketObservationId" TEXT NULL,
                "DataAsOfDate" TEXT NOT NULL DEFAULT '0001-01-01',
                "AsOfDate" TEXT NOT NULL,
                "RawValue" TEXT NOT NULL,
                "NormalizedValue" TEXT NOT NULL,
                "ZScore" TEXT NOT NULL,
                "Momentum4Weeks" TEXT NOT NULL,
                "Interpretation" TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "RegimeModels" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_RegimeModels" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "Name" TEXT NOT NULL,
                "Kind" TEXT NOT NULL,
                "IsProduction" INTEGER NOT NULL,
                "Notes" TEXT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "RegimeModelVersions" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_RegimeModelVersions" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "RegimeModelId" TEXT NOT NULL,
                "Version" TEXT NOT NULL,
                "Description" TEXT NULL,
                "ParametersJson" TEXT NULL,
                "EffectiveFrom" TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "RegimeRuns" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_RegimeRuns" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "RegimeModelVersionId" TEXT NOT NULL,
                "RunDate" TEXT NOT NULL,
                "AsOfDate" TEXT NOT NULL,
                "PrimaryRegime" INTEGER NOT NULL,
                "Confidence" TEXT NOT NULL,
                "CompositeScore" TEXT NOT NULL,
                "Status" TEXT NOT NULL,
                "Summary" TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "RegimeProbabilities" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_RegimeProbabilities" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "RegimeRunId" TEXT NOT NULL,
                "Regime" INTEGER NOT NULL,
                "Probability" TEXT NOT NULL,
                "Rank" INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "RegimeExplanations" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_RegimeExplanations" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "RegimeRunId" TEXT NOT NULL,
                "Title" TEXT NOT NULL,
                "Detail" TEXT NOT NULL,
                "Impact" TEXT NOT NULL,
                "FeatureCode" TEXT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "RegimeReports" (
                "Id" TEXT NOT NULL CONSTRAINT "PK_RegimeReports" PRIMARY KEY,
                "CreatedAt" TEXT NOT NULL,
                "UpdatedAt" TEXT NULL,
                "RegimeRunId" TEXT NOT NULL,
                "ReportDate" TEXT NOT NULL,
                "Title" TEXT NOT NULL,
                "Narrative" TEXT NOT NULL,
                "RecommendedAction" TEXT NOT NULL,
                "ReviewRequired" INTEGER NOT NULL
            )
            """
        };

        foreach (var statement in statements)
        {
            await dbContext.Database.ExecuteSqlRawAsync(statement, cancellationToken);
        }

        await EnsureColumnAsync(dbContext, "MacroDataSources", "ApiBaseUrl", "TEXT NULL", cancellationToken);
        await EnsureColumnAsync(dbContext, "MacroDataSources", "SupportsVintageData", "INTEGER NOT NULL DEFAULT 0", cancellationToken);
        await EnsureColumnAsync(dbContext, "MacroSeries", "FredSeriesId", "TEXT NULL", cancellationToken);
        await EnsureColumnAsync(dbContext, "MacroSeries", "FredMdColumn", "TEXT NULL", cancellationToken);
        await EnsureColumnAsync(dbContext, "MacroSeries", "RequiresVintageTracking", "INTEGER NOT NULL DEFAULT 1", cancellationToken);
        await EnsureColumnAsync(dbContext, "MacroObservations", "DataVintageId", "TEXT NULL", cancellationToken);
        await EnsureColumnAsync(dbContext, "MacroFeatureValues", "MacroObservationId", "TEXT NULL", cancellationToken);
        await EnsureColumnAsync(dbContext, "MacroFeatureValues", "MarketObservationId", "TEXT NULL", cancellationToken);
        await EnsureColumnAsync(dbContext, "MacroFeatureValues", "DataAsOfDate", "TEXT NOT NULL DEFAULT '0001-01-01'", cancellationToken);
    }

    public static async Task SeedAsync(FinanceDbContext dbContext, CancellationToken cancellationToken = default)
    {
        var eur = await EnsureCurrencyAsync(dbContext, "EUR", "Euro", "EUR", cancellationToken);
        var usd = await EnsureCurrencyAsync(dbContext, "USD", "US Dollar", "USD", cancellationToken);

        var equity = await EnsureAssetClassAsync(dbContext, "EQUITY", "Azioni", cancellationToken);
        var bonds = await EnsureAssetClassAsync(dbContext, "BONDS", "Obbligazioni", cancellationToken);
        var cash = await EnsureAssetClassAsync(dbContext, "CASH", "Liquidita", cancellationToken);
        var inflation = await EnsureAssetClassAsync(dbContext, "INFLATION", "Inflation hedge", cancellationToken);
        var commodities = await EnsureAssetClassAsync(dbContext, "COMMODITIES", "Materie prime", cancellationToken);
        var realEstate = await EnsureAssetClassAsync(dbContext, "REAL_ESTATE", "Immobiliare", cancellationToken);

        var owner = await dbContext.Owners.FirstOrDefaultAsync(x => x.DisplayName == "Investitore Demo", cancellationToken)
            ?? dbContext.Owners.Add(new Owner { DisplayName = "Investitore Demo", Email = "demo@example.local" }).Entity;

        var portfolio = await dbContext.Portfolios
            .Include(x => x.Accounts)
            .FirstOrDefaultAsync(x => x.Name == "Portafoglio Personale", cancellationToken);

        if (portfolio is null)
        {
            portfolio = dbContext.Portfolios.Add(new Portfolio
            {
                Name = "Portafoglio Personale",
                Owner = owner,
                BaseCurrency = eur
            }).Entity;
        }

        var cashAccount = await EnsureAccountAsync(dbContext, portfolio, eur, "Conto liquidita EUR", AccountType.Cash, cancellationToken);
        var securitiesAccount = await EnsureAccountAsync(dbContext, portfolio, eur, "Deposito titoli", AccountType.Securities, cancellationToken);

        var worldEtf = await EnsureInstrumentAsync(dbContext, "WORLD", "ETF Azionario Globale Demo", "DEMO", InstrumentType.Etf, eur, equity, cancellationToken);
        var bondEtf = await EnsureInstrumentAsync(dbContext, "BOND", "ETF Obbligazionario Demo", "DEMO", InstrumentType.Etf, eur, bonds, cancellationToken);
        var moneyMarket = await EnsureInstrumentAsync(dbContext, "MMKT", "Fondo monetario EUR Demo", "DEMO", InstrumentType.Fund, eur, cash, cancellationToken);
        var gold = await EnsureInstrumentAsync(dbContext, "GOLD", "ETC Oro Demo", "DEMO", InstrumentType.Commodity, usd, commodities, cancellationToken);
        var reit = await EnsureInstrumentAsync(dbContext, "REIT", "REIT Globale Demo", "DEMO", InstrumentType.Equity, usd, realEstate, cancellationToken);

        await EnsureTargetAllocationAsync(dbContext, portfolio, equity, 0.60m, 0.50m, 0.70m, cancellationToken);
        await EnsureTargetAllocationAsync(dbContext, portfolio, bonds, 0.30m, 0.20m, 0.40m, cancellationToken);
        await EnsureTargetAllocationAsync(dbContext, portfolio, cash, 0.05m, 0.02m, 0.12m, cancellationToken);
        await EnsureTargetAllocationAsync(dbContext, portfolio, inflation, 0.05m, 0.00m, 0.12m, cancellationToken);

        await EnsurePolicyAsync(dbContext, portfolio, cancellationToken);
        var regime = await EnsureRegimeAsync(dbContext, cancellationToken);
        await EnsureProposalAsync(dbContext, portfolio, regime, equity, bonds, cash, cancellationToken);
        await EnsureMacroRegimeEngineSeedAsync(dbContext, cancellationToken);

        var today = DateOnly.FromDateTime(DateTime.Today);
        var historyStart = today.AddDays(-45);
        await EnsurePriceHistoryAsync(dbContext, worldEtf, eur, historyStart, today, 100m, 0.33m, 1.8m, cancellationToken);
        await EnsurePriceHistoryAsync(dbContext, bondEtf, eur, historyStart, today, 100m, 0.08m, 0.55m, cancellationToken);
        await EnsurePriceHistoryAsync(dbContext, moneyMarket, eur, historyStart, today, 100m, 0.02m, 0.08m, cancellationToken);
        await EnsurePriceHistoryAsync(dbContext, gold, usd, historyStart, today, 190m, 0.18m, 2.2m, cancellationToken);
        await EnsurePriceHistoryAsync(dbContext, reit, usd, historyStart, today, 72m, -0.04m, 1.4m, cancellationToken);
        await EnsureFxHistoryAsync(dbContext, usd, eur, historyStart, today, cancellationToken);

        if (!await dbContext.Transactions.AnyAsync(cancellationToken))
        {
            dbContext.Transactions.AddRange(
                new Transaction
                {
                    TradeDate = today.AddDays(-20),
                    SettlementDate = today.AddDays(-20),
                    Type = TransactionType.Deposit,
                    Portfolio = portfolio,
                    CashAccount = cashAccount,
                    Quantity = 0m,
                    Price = 1m,
                    PriceCurrency = eur,
                    GrossAmount = 10000m,
                    Notes = "Deposito iniziale demo",
                    ImportSource = "Seed"
                },
                new Transaction
                {
                    TradeDate = today.AddDays(-15),
                    SettlementDate = today.AddDays(-13),
                    Type = TransactionType.Buy,
                    Portfolio = portfolio,
                    Instrument = worldEtf,
                    CashAccount = cashAccount,
                    SecuritiesAccount = securitiesAccount,
                    Quantity = 45m,
                    Price = 100m,
                    PriceCurrency = eur,
                    GrossAmount = -4500m,
                    Fees = 3m,
                    Taxes = 0m,
                    Notes = "Acquisto ETF azionario demo",
                    ImportSource = "Seed"
                },
                new Transaction
                {
                    TradeDate = today.AddDays(-12),
                    SettlementDate = today.AddDays(-10),
                    Type = TransactionType.Buy,
                    Portfolio = portfolio,
                    Instrument = bondEtf,
                    CashAccount = cashAccount,
                    SecuritiesAccount = securitiesAccount,
                    Quantity = 28m,
                    Price = 100m,
                    PriceCurrency = eur,
                    GrossAmount = -2800m,
                    Fees = 3m,
                    Taxes = 0m,
                    Notes = "Acquisto ETF obbligazionario demo",
                    ImportSource = "Seed"
                },
                new Transaction
                {
                    TradeDate = today.AddDays(-5),
                    SettlementDate = today.AddDays(-5),
                    Type = TransactionType.Buy,
                    Portfolio = portfolio,
                    Instrument = moneyMarket,
                    CashAccount = cashAccount,
                    SecuritiesAccount = securitiesAccount,
                    Quantity = 12m,
                    Price = 100m,
                    PriceCurrency = eur,
                    GrossAmount = -1200m,
                    Fees = 1m,
                    Taxes = 0m,
                    Notes = "Allocazione liquidita investibile demo",
                    ImportSource = "Seed"
                });
        }

        if (!await dbContext.AuditEvents.AnyAsync(cancellationToken))
        {
            dbContext.AuditEvents.Add(new AuditEvent
            {
                Area = "Seed",
                EventType = "DemoDataInitialized",
                Message = "Dati demo iniziali creati per fase 1 e ledger portafoglio.",
                Actor = "system"
            });
        }

        if (!await dbContext.AuditEvents.AnyAsync(x => x.Area == "Seed" && x.EventType == "MarketDataSeeded", cancellationToken))
        {
            dbContext.AuditEvents.Add(new AuditEvent
            {
                Area = "Seed",
                EventType = "MarketDataSeeded",
                Message = "Prezzi storici e FX demo creati per la fase performance.",
                Actor = "system"
            });
        }

        await dbContext.SaveChangesAsync(cancellationToken);
    }

    private static async Task EnsureColumnAsync(FinanceDbContext dbContext, string tableName, string columnName, string definition, CancellationToken cancellationToken)
    {
        var connection = dbContext.Database.GetDbConnection();
        if (connection.State != System.Data.ConnectionState.Open)
        {
            await connection.OpenAsync(cancellationToken);
        }

        await using var checkCommand = connection.CreateCommand();
        checkCommand.CommandText = $"PRAGMA table_info(\"{tableName}\")";
        await using var reader = await checkCommand.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            if (string.Equals(reader.GetString(1), columnName, StringComparison.OrdinalIgnoreCase))
            {
                return;
            }
        }

        var safeTableName = tableName.Replace("\"", "\"\"", StringComparison.Ordinal);
        var safeColumnName = columnName.Replace("\"", "\"\"", StringComparison.Ordinal);
        var sql = "ALTER TABLE \"" + safeTableName + "\" ADD COLUMN \"" + safeColumnName + "\" " + definition;
        await dbContext.Database.ExecuteSqlRawAsync(sql, cancellationToken);
    }

    private static async Task<Currency> EnsureCurrencyAsync(FinanceDbContext dbContext, string code, string name, string symbol, CancellationToken cancellationToken)
    {
        return await dbContext.Currencies.FirstOrDefaultAsync(x => x.Code == code, cancellationToken)
            ?? dbContext.Currencies.Add(new Currency { Code = code, Name = name, Symbol = symbol }).Entity;
    }

    private static async Task<MacroDataSource> EnsureMacroDataSourceAsync(
        FinanceDbContext dbContext,
        string name,
        string kind,
        string? url,
        string? apiBaseUrl,
        bool supportsVintageData,
        string? notes,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.MacroDataSources.FirstOrDefaultAsync(x => x.Name == name, cancellationToken);
        if (existing is not null)
        {
            existing.Kind = kind;
            existing.Url = url;
            existing.ApiBaseUrl = apiBaseUrl;
            existing.SupportsVintageData = supportsVintageData;
            existing.Notes = notes;
            return existing;
        }

        return dbContext.MacroDataSources.Add(new MacroDataSource
        {
            Name = name,
            Kind = kind,
            Url = url,
            ApiBaseUrl = apiBaseUrl,
            SupportsVintageData = supportsVintageData,
            Notes = notes
        }).Entity;
    }

    private static async Task<AssetClass> EnsureAssetClassAsync(FinanceDbContext dbContext, string code, string name, CancellationToken cancellationToken)
    {
        return await dbContext.AssetClasses.FirstOrDefaultAsync(x => x.Code == code, cancellationToken)
            ?? dbContext.AssetClasses.Add(new AssetClass { Code = code, Name = name }).Entity;
    }

    private static async Task<Account> EnsureAccountAsync(
        FinanceDbContext dbContext,
        Portfolio portfolio,
        Currency currency,
        string name,
        AccountType type,
        CancellationToken cancellationToken)
    {
        return await dbContext.Accounts.FirstOrDefaultAsync(x => x.PortfolioId == portfolio.Id && x.Name == name, cancellationToken)
            ?? dbContext.Accounts.Add(new Account
            {
                Name = name,
                Type = type,
                Portfolio = portfolio,
                Currency = currency,
                BrokerName = "Demo Broker"
            }).Entity;
    }

    private static async Task<Instrument> EnsureInstrumentAsync(
        FinanceDbContext dbContext,
        string symbol,
        string name,
        string exchange,
        InstrumentType type,
        Currency currency,
        AssetClass assetClass,
        CancellationToken cancellationToken)
    {
        return await dbContext.Instruments.FirstOrDefaultAsync(x => x.Symbol == symbol && x.Exchange == exchange, cancellationToken)
            ?? dbContext.Instruments.Add(new Instrument
            {
                Symbol = symbol,
                Name = name,
                Exchange = exchange,
                Type = type,
                Currency = currency,
                AssetClass = assetClass
            }).Entity;
    }

    private static async Task EnsureTargetAllocationAsync(
        FinanceDbContext dbContext,
        Portfolio portfolio,
        AssetClass assetClass,
        decimal target,
        decimal minimum,
        decimal maximum,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.TargetAllocations
            .FirstOrDefaultAsync(x => x.PortfolioId == portfolio.Id && x.AssetClassId == assetClass.Id, cancellationToken);

        if (existing is not null)
        {
            existing.TargetWeight = target;
            existing.MinimumWeight = minimum;
            existing.MaximumWeight = maximum;
            return;
        }

        dbContext.TargetAllocations.Add(new TargetAllocation
        {
            Portfolio = portfolio,
            AssetClass = assetClass,
            TargetWeight = target,
            MinimumWeight = minimum,
            MaximumWeight = maximum
        });
    }

    private static async Task EnsurePriceHistoryAsync(
        FinanceDbContext dbContext,
        Instrument instrument,
        Currency currency,
        DateOnly startDate,
        DateOnly endDate,
        decimal startClose,
        decimal dailyTrend,
        decimal cycleAmplitude,
        CancellationToken cancellationToken)
    {
        for (var date = startDate; date <= endDate; date = date.AddDays(1))
        {
            var index = date.DayNumber - startDate.DayNumber;
            var cycle = (decimal)Math.Sin(index / 4d) * cycleAmplitude;
            var close = Math.Max(0.01m, Math.Round(startClose + (dailyTrend * index) + cycle, 4));
            var existing = await dbContext.Prices
                .FirstOrDefaultAsync(x => x.InstrumentId == instrument.Id && x.Date == date, cancellationToken);

            if (existing is not null)
            {
                existing.Close = close;
                existing.Currency = currency;
                existing.Source = "Seed";
                continue;
            }

            dbContext.Prices.Add(new Price
            {
                Instrument = instrument,
                Date = date,
                Close = close,
                Currency = currency,
                Source = "Seed"
            });
        }
    }

    private static async Task EnsureFxHistoryAsync(
        FinanceDbContext dbContext,
        Currency fromCurrency,
        Currency toCurrency,
        DateOnly startDate,
        DateOnly endDate,
        CancellationToken cancellationToken)
    {
        for (var date = startDate; date <= endDate; date = date.AddDays(1))
        {
            var index = date.DayNumber - startDate.DayNumber;
            var rate = Math.Round(0.91m + ((decimal)Math.Sin(index / 5d) * 0.012m), 6);
            var existing = await dbContext.FxRates.FirstOrDefaultAsync(
                x => x.FromCurrencyId == fromCurrency.Id && x.ToCurrencyId == toCurrency.Id && x.Date == date,
                cancellationToken);

            if (existing is not null)
            {
                existing.Rate = rate;
                existing.Source = "Seed";
                continue;
            }

            dbContext.FxRates.Add(new FxRate
            {
                Date = date,
                FromCurrency = fromCurrency,
                ToCurrency = toCurrency,
                Rate = rate,
                Source = "Seed"
            });
        }
    }

    private static async Task EnsurePolicyAsync(FinanceDbContext dbContext, Portfolio portfolio, CancellationToken cancellationToken)
    {
        if (await dbContext.PortfolioPolicies.AnyAsync(x => x.PortfolioId == portfolio.Id && x.IsActive, cancellationToken))
        {
            return;
        }

        dbContext.PortfolioPolicies.Add(new PortfolioPolicy
        {
            Portfolio = portfolio,
            Name = "Policy strategica demo",
            CashBufferWeight = 0.05m,
            MaxTurnoverPerRebalance = 0.15m,
            MinimumTradeAmountBase = 250m,
            TaxAwareRebalancing = true
        });
    }

    private static async Task<RegimeObservation> EnsureRegimeAsync(FinanceDbContext dbContext, CancellationToken cancellationToken)
    {
        var today = DateOnly.FromDateTime(DateTime.Today);
        var regime = await dbContext.RegimeObservations.FirstOrDefaultAsync(x => x.ObservationDate == today, cancellationToken);
        if (regime is not null)
        {
            return regime;
        }

        regime = dbContext.RegimeObservations.Add(new RegimeObservation
        {
            ObservationDate = today,
            Regime = RegimeType.UncertainTransition,
            Probability = 0.58m,
            Summary = "Regime iniziale incerto/transizione",
            Explanation = "Seed dimostrativo: i segnali macro e mercato devono essere importati prima di usare la strategia in produzione."
        }).Entity;

        dbContext.RegimeSignals.AddRange(
            new RegimeSignal { RegimeObservation = regime, Name = "Growth momentum", Dimension = "Crescita", Value = 0m, ZScore = 0m, Interpretation = "Da alimentare con dati macro" },
            new RegimeSignal { RegimeObservation = regime, Name = "Inflation pressure", Dimension = "Inflazione", Value = 0m, ZScore = 0m, Interpretation = "Da alimentare con dati macro" });

        return regime;
    }

    private static async Task EnsureProposalAsync(
        FinanceDbContext dbContext,
        Portfolio portfolio,
        RegimeObservation regime,
        AssetClass equity,
        AssetClass bonds,
        AssetClass cash,
        CancellationToken cancellationToken)
    {
        if (await dbContext.AllocationProposals.AnyAsync(x => x.PortfolioId == portfolio.Id, cancellationToken))
        {
            return;
        }

        var proposal = dbContext.AllocationProposals.Add(new AllocationProposal
        {
            Portfolio = portfolio,
            RegimeObservation = regime,
            ProposalDate = DateOnly.FromDateTime(DateTime.Today),
            Decision = "Attendere conferma",
            Rationale = "La policy centrale resta l'ancora finche' il regime non supera le soglie di conferma.",
            EstimatedCostBase = 0m,
            EstimatedTaxImpactBase = 0m
        }).Entity;

        dbContext.RebalanceRecommendations.AddRange(
            new RebalanceRecommendation { AllocationProposal = proposal, AssetClass = equity, Action = RebalanceAction.Hold, CurrentWeight = 0.60m, TargetWeight = 0.60m, TradeAmountBase = 0m },
            new RebalanceRecommendation { AllocationProposal = proposal, AssetClass = bonds, Action = RebalanceAction.Hold, CurrentWeight = 0.30m, TargetWeight = 0.30m, TradeAmountBase = 0m },
            new RebalanceRecommendation { AllocationProposal = proposal, AssetClass = cash, Action = RebalanceAction.Hold, CurrentWeight = 0.05m, TargetWeight = 0.05m, TradeAmountBase = 0m });
    }

    private static async Task EnsureMacroRegimeEngineSeedAsync(FinanceDbContext dbContext, CancellationToken cancellationToken)
    {
        var today = DateOnly.FromDateTime(DateTime.Today);

        var fred = await EnsureMacroDataSourceAsync(dbContext, "FRED", "MacroApi", "https://fred.stlouisfed.org", "https://api.stlouisfed.org/fred", true, "Fonte macroeconomica primaria per serie FRED e calendario rilasci.", cancellationToken);
        var alfred = await EnsureMacroDataSourceAsync(dbContext, "ALFRED", "MacroVintageApi", "https://alfred.stlouisfed.org", "https://api.stlouisfed.org/fred", true, "Fonte per vintage real-time delle serie macro quando disponibile.", cancellationToken);
        var fredMd = await EnsureMacroDataSourceAsync(dbContext, "FRED-MD", "MacroDataset", "https://research.stlouisfed.org/econ/mccracken/fred-databases/", null, true, "Dataset macro ampio per clustering/HMM e feature store.", cancellationToken);
        var market = await EnsureMacroDataSourceAsync(dbContext, "MarketDataDemo", "MarketData", null, null, false, "Proxy cross-asset demo per risk, credit, FX, commodity ed ETF.", cancellationToken);

        var ism = await EnsureMacroSeriesAsync(dbContext, fred, "ISM_PMI", "ISM Manufacturing PMI", "Growth", "Monthly", "Index", true, 3, cancellationToken);
        var sahm = await EnsureMacroSeriesAsync(dbContext, fred, "SAHM", "Sahm Rule Recession Indicator", "Growth", "Monthly", "Percentage points", false, 3, cancellationToken);
        var breakeven = await EnsureMacroSeriesAsync(dbContext, fred, "T10YIE", "10Y Breakeven Inflation Rate", "Inflation", "Daily", "Percent", true, 1, cancellationToken);
        var hySpread = await EnsureMacroSeriesAsync(dbContext, fred, "HY_OAS", "US High Yield Option-Adjusted Spread", "Credit", "Daily", "Basis points", false, 1, cancellationToken);
        var curve = await EnsureMacroSeriesAsync(dbContext, fred, "YC_10Y2Y", "10Y minus 2Y Treasury Spread", "Monetary", "Daily", "Percent", true, 1, cancellationToken);
        var vix = await EnsureMacroSeriesAsync(dbContext, market, "VIX", "CBOE Volatility Index", "Risk", "Daily", "Index", false, 0, cancellationToken);
        await EnsureMacroSeriesAsync(dbContext, fredMd, "FREDMD_INDPRO", "FRED-MD Industrial Production", "Growth", "Monthly", "Index", true, 15, cancellationToken);

        await EnsureMacroObservationAsync(dbContext, ism, today.AddMonths(-1), today.AddMonths(-1).AddDays(3), 51.2m, "seed-2026-07", cancellationToken);
        await EnsureMacroObservationAsync(dbContext, sahm, today.AddMonths(-1), today.AddMonths(-1).AddDays(3), 0.22m, "seed-2026-07", cancellationToken);
        await EnsureMacroObservationAsync(dbContext, breakeven, today.AddDays(-1), today, 2.36m, "seed-2026-07", cancellationToken);
        await EnsureMacroObservationAsync(dbContext, hySpread, today.AddDays(-1), today, 355m, "seed-2026-07", cancellationToken);
        await EnsureMacroObservationAsync(dbContext, curve, today.AddDays(-1), today, 0.18m, "seed-2026-07", cancellationToken);
        await EnsureMacroObservationAsync(dbContext, vix, today.AddDays(-1), today, 17.8m, "seed-2026-07", cancellationToken);
        await EnsureReleaseCalendarAsync(dbContext, fred, "ISM", "ISM Manufacturing PMI", today.AddMonths(-1).AddDays(3), today.AddMonths(-1), today.AddMonths(-1), "Monthly", "Seeded", cancellationToken);
        await EnsureReleaseCalendarAsync(dbContext, fred, "SAHM", "Sahm Rule Recession Indicator", today.AddMonths(-1).AddDays(3), today.AddMonths(-1), today.AddMonths(-1), "Monthly", "Seeded", cancellationToken);
        await EnsureReleaseCalendarAsync(dbContext, alfred, "VINTAGE", "ALFRED real-time vintage availability", today, today.AddDays(-1), today.AddDays(-1), "AdHoc", "Seeded", cancellationToken);

        var eurUsd = await EnsureMarketSeriesAsync(dbContext, market, "EURUSD", "EUR/USD FX proxy", "FX", "Daily", "Rate", "USD", "FX", "FX", false, cancellationToken);
        var goldProxy = await EnsureMarketSeriesAsync(dbContext, market, "GLD", "Gold ETF proxy", "Commodity", "Daily", "Price", "USD", "COMMODITIES", "Commodity", false, cancellationToken);
        var worldProxy = await EnsureMarketSeriesAsync(dbContext, market, "VWCE_PROXY", "Global equity ETF proxy", "ETF", "Daily", "Price", "EUR", "EQUITY", "ETF", true, cancellationToken);
        var treasuryProxy = await EnsureMarketSeriesAsync(dbContext, market, "IEF_PROXY", "Intermediate Treasury ETF proxy", "ETF", "Daily", "Price", "USD", "BONDS", "Rates", false, cancellationToken);
        var creditProxy = await EnsureMarketSeriesAsync(dbContext, market, "JNK_LQD", "High yield vs investment grade credit proxy", "Credit", "Daily", "Ratio", "USD", "BONDS", "Credit", true, cancellationToken);
        await EnsureMarketObservationAsync(dbContext, eurUsd, today.AddDays(-1), 1.082m, today, "seed", cancellationToken);
        await EnsureMarketObservationAsync(dbContext, goldProxy, today.AddDays(-1), 212.4m, today, "seed", cancellationToken);
        await EnsureMarketObservationAsync(dbContext, worldProxy, today.AddDays(-1), 118.7m, today, "seed", cancellationToken);
        await EnsureMarketObservationAsync(dbContext, treasuryProxy, today.AddDays(-1), 94.2m, today, "seed", cancellationToken);
        await EnsureMarketObservationAsync(dbContext, creditProxy, today.AddDays(-1), 0.74m, today, "seed", cancellationToken);

        var featureSet = await dbContext.MacroFeatureSetVersions.FirstOrDefaultAsync(x => x.Name == "CRS Baseline" && x.Version == "v0.1", cancellationToken)
            ?? dbContext.MacroFeatureSetVersions.Add(new MacroFeatureSetVersion
            {
                Name = "CRS Baseline",
                Version = "v0.1",
                Description = "Baseline rule-based ispirata a Growth, Inflation, Risk e Monetary score.",
                IsActive = true
            }).Entity;

        var growth = await EnsureFeatureDefinitionAsync(dbContext, featureSet, "GROWTH_MOM", "Growth momentum", "Growth", "Rank(ISM PMI) e filtro Sahm inverso", 0.30m, 60, true, cancellationToken);
        var inflation = await EnsureFeatureDefinitionAsync(dbContext, featureSet, "INFL_PRESS", "Inflation pressure", "Inflation", "Rank breakeven e proxy commodity/inflation hedge", 0.25m, 60, false, cancellationToken);
        var risk = await EnsureFeatureDefinitionAsync(dbContext, featureSet, "RISK_APPETITE", "Risk appetite", "Risk", "Rank inverso VIX e HY OAS", 0.25m, 60, true, cancellationToken);
        var monetary = await EnsureFeatureDefinitionAsync(dbContext, featureSet, "MONETARY_COND", "Monetary conditions", "Monetary", "Yield curve e policy stance", 0.15m, 60, true, cancellationToken);
        var credit = await EnsureFeatureDefinitionAsync(dbContext, featureSet, "CREDIT_STRESS", "Credit stress", "Credit", "HY spread normalizzato e momentum credito", 0.05m, 60, false, cancellationToken);

        await EnsureFeatureValueAsync(dbContext, growth, today, 51.2m, 0.56m, 0.18m, 0.04m, "Crescita moderata, non recessiva.", cancellationToken);
        await EnsureFeatureValueAsync(dbContext, inflation, today, 2.36m, 0.62m, 0.44m, 0.07m, "Pressione inflattiva ancora presente, ma non estrema.", cancellationToken);
        await EnsureFeatureValueAsync(dbContext, risk, today, 17.8m, 0.58m, 0.25m, -0.03m, "Risk appetite neutrale con volatilita' contenuta.", cancellationToken);
        await EnsureFeatureValueAsync(dbContext, monetary, today, 0.18m, 0.47m, -0.12m, 0.02m, "Condizioni monetarie non pienamente accomodanti.", cancellationToken);
        await EnsureFeatureValueAsync(dbContext, credit, today, 355m, 0.52m, 0.05m, -0.01m, "Credito sotto controllo ma da monitorare.", cancellationToken);

        var model = await dbContext.RegimeModels.FirstOrDefaultAsync(x => x.Name == "CRS Rule-Based Engine", cancellationToken)
            ?? dbContext.RegimeModels.Add(new RegimeModel
            {
                Name = "CRS Rule-Based Engine",
                Kind = "RuleBased",
                IsProduction = true,
                Notes = "Baseline interpretabile della Fase 6; HMM/clustering entreranno come challenger."
            }).Entity;

        var version = await dbContext.RegimeModelVersions.FirstOrDefaultAsync(x => x.RegimeModelId == model.Id && x.Version == "v0.1", cancellationToken)
            ?? dbContext.RegimeModelVersions.Add(new RegimeModelVersion
            {
                RegimeModel = model,
                Version = "v0.1",
                EffectiveFrom = today,
                Description = "Prima versione demo con feature store e probabilita' euristiche.",
                ParametersJson = """{"confirmationWeeks":4,"transitionSpeedThreshold":0.15,"uncertainBelowConfidence":0.60}"""
            }).Entity;

        if (await dbContext.RegimeRuns.AnyAsync(x => x.RegimeModelVersionId == version.Id && x.AsOfDate == today, cancellationToken))
        {
            return;
        }

        var run = dbContext.RegimeRuns.Add(new RegimeRun
        {
            RegimeModelVersion = version,
            RunDate = today,
            AsOfDate = today,
            PrimaryRegime = RegimeType.UncertainTransition,
            Confidence = 0.57m,
            CompositeScore = 0.56m,
            Status = "Transition",
            Summary = "Regime centrale vicino a Goldilocks/Reflation, ma confidence insufficiente per tilt pieno."
        }).Entity;

        dbContext.RegimeProbabilities.AddRange(
            new RegimeProbability { RegimeRun = run, Regime = RegimeType.Goldilocks, Probability = 0.34m, Rank = 1 },
            new RegimeProbability { RegimeRun = run, Regime = RegimeType.Reflation, Probability = 0.26m, Rank = 2 },
            new RegimeProbability { RegimeRun = run, Regime = RegimeType.UncertainTransition, Probability = 0.22m, Rank = 3 },
            new RegimeProbability { RegimeRun = run, Regime = RegimeType.Stagflation, Probability = 0.11m, Rank = 4 },
            new RegimeProbability { RegimeRun = run, Regime = RegimeType.DeflationBust, Probability = 0.07m, Rank = 5 });

        dbContext.RegimeExplanations.AddRange(
            new RegimeExplanation { RegimeRun = run, Title = "Growth stabile", Detail = "PMI sopra area contrazione e Sahm sotto soglia rossa sostengono lo scenario non recessivo.", Impact = 0.18m, FeatureCode = "GROWTH_MOM" },
            new RegimeExplanation { RegimeRun = run, Title = "Inflazione non completamente normalizzata", Detail = "Breakeven e proxy inflation hedge impediscono una classificazione Goldilocks piena.", Impact = -0.09m, FeatureCode = "INFL_PRESS" },
            new RegimeExplanation { RegimeRun = run, Title = "Credito da monitorare", Detail = "HY spread non segnala stress acuto, ma resta un driver chiave per eventuale transizione risk-off.", Impact = -0.04m, FeatureCode = "CREDIT_STRESS" });

        dbContext.RegimeReports.Add(new RegimeReport
        {
            RegimeRun = run,
            ReportDate = today,
            Title = "Report regime-aware demo",
            Narrative = "Il motore baseline legge un contesto moderatamente favorevole ma non abbastanza coerente per un cambio allocativo aggressivo. La policy centrale resta l'ancora operativa.",
            RecommendedAction = "Mantenere allocazione strategica, consentendo solo tilt parziali tramite nuovi contributi o ribilanciamenti naturali.",
            ReviewRequired = false
        });

        dbContext.AuditEvents.Add(new AuditEvent
        {
            Area = "MacroRegime",
            EventType = "PhaseSixSeeded",
            Message = "Seed demo Macro-Regime Engine creato con feature store, modello baseline e report regime-aware.",
            Actor = "system"
        });
    }

    private static async Task<MacroSeries> EnsureMacroSeriesAsync(
        FinanceDbContext dbContext,
        MacroDataSource source,
        string code,
        string name,
        string category,
        string frequency,
        string unit,
        bool isHigherRiskOn,
        int publicationLagDays,
        CancellationToken cancellationToken)
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
            PublicationLagDays = publicationLagDays,
            FredSeriesId = source.Name == "FRED" ? code : null,
            FredMdColumn = source.Name == "FRED-MD" ? code : null,
            RequiresVintageTracking = source.SupportsVintageData
        }).Entity;
    }

    private static async Task EnsureMacroObservationAsync(
        FinanceDbContext dbContext,
        MacroSeries series,
        DateOnly observationDate,
        DateOnly publishedDate,
        decimal value,
        string vintage,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.MacroObservations.FirstOrDefaultAsync(x => x.MacroSeriesId == series.Id && x.ObservationDate == observationDate && x.Vintage == vintage, cancellationToken);
        if (existing is not null)
        {
            existing.DataVintage ??= await EnsureSeedDataVintageAsync(dbContext, series, publishedDate, vintage, cancellationToken);
            existing.PublishedDate = publishedDate;
            existing.Value = value;
            return;
        }

        dbContext.MacroObservations.Add(new MacroObservation
        {
            MacroSeries = series,
            DataVintage = await EnsureSeedDataVintageAsync(dbContext, series, publishedDate, vintage, cancellationToken),
            ObservationDate = observationDate,
            PublishedDate = publishedDate,
            Value = value,
            Vintage = vintage,
            IsRevised = false
        });
    }

    private static async Task<DataVintage> EnsureSeedDataVintageAsync(
        FinanceDbContext dbContext,
        MacroSeries series,
        DateOnly publishedDate,
        string vintageLabel,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.DataVintages.FirstOrDefaultAsync(
            x => x.MacroSeriesId == series.Id && x.VintageDate == publishedDate && x.RealtimeStart == publishedDate && x.RealtimeEnd == publishedDate,
            cancellationToken);

        if (existing is not null)
        {
            return existing;
        }

        return dbContext.DataVintages.Add(new DataVintage
        {
            MacroSeries = series,
            VintageDate = publishedDate,
            RealtimeStart = publishedDate,
            RealtimeEnd = publishedDate,
            SourceSystem = "Seed",
            SourceUrl = vintageLabel,
            SourceHash = vintageLabel,
            IsOfficialVintage = false
        }).Entity;
    }

    private static async Task EnsureReleaseCalendarAsync(
        FinanceDbContext dbContext,
        MacroDataSource source,
        string releaseCode,
        string name,
        DateOnly releaseDate,
        DateOnly? observationPeriodStart,
        DateOnly? observationPeriodEnd,
        string frequency,
        string status,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.ReleaseCalendar.FirstOrDefaultAsync(
            x => x.MacroDataSourceId == source.Id && x.ReleaseCode == releaseCode && x.ReleaseDate == releaseDate,
            cancellationToken);

        if (existing is not null)
        {
            existing.Name = name;
            existing.ObservationPeriodStart = observationPeriodStart;
            existing.ObservationPeriodEnd = observationPeriodEnd;
            existing.Frequency = frequency;
            existing.Status = status;
            return;
        }

        dbContext.ReleaseCalendar.Add(new ReleaseCalendar
        {
            MacroDataSource = source,
            ReleaseCode = releaseCode,
            Name = name,
            ReleaseDate = releaseDate,
            ObservationPeriodStart = observationPeriodStart,
            ObservationPeriodEnd = observationPeriodEnd,
            Frequency = frequency,
            Status = status
        });
    }

    private static async Task<MarketSeries> EnsureMarketSeriesAsync(
        FinanceDbContext dbContext,
        MacroDataSource source,
        string symbol,
        string name,
        string category,
        string frequency,
        string unit,
        string currencyCode,
        string assetClassCode,
        string proxyRole,
        bool isHigherRiskOn,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.MarketSeries.FirstOrDefaultAsync(x => x.Symbol == symbol, cancellationToken);
        if (existing is not null)
        {
            existing.Name = name;
            existing.Category = category;
            existing.Frequency = frequency;
            existing.Unit = unit;
            existing.CurrencyCode = currencyCode;
            existing.AssetClassCode = assetClassCode;
            existing.ProxyRole = proxyRole;
            existing.IsHigherRiskOn = isHigherRiskOn;
            existing.IsProxy = true;
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
            CurrencyCode = currencyCode,
            AssetClassCode = assetClassCode,
            ProxyRole = proxyRole,
            IsHigherRiskOn = isHigherRiskOn,
            IsProxy = true
        }).Entity;
    }

    private static async Task EnsureMarketObservationAsync(
        FinanceDbContext dbContext,
        MarketSeries series,
        DateOnly date,
        decimal value,
        DateOnly availableDate,
        string sourceHash,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.MarketObservations.FirstOrDefaultAsync(x => x.MarketSeriesId == series.Id && x.Date == date, cancellationToken);
        if (existing is not null)
        {
            existing.Value = value;
            existing.AvailableDate = availableDate;
            existing.SourceHash = sourceHash;
            return;
        }

        dbContext.MarketObservations.Add(new MarketObservation
        {
            MarketSeries = series,
            Date = date,
            Value = value,
            AvailableDate = availableDate,
            SourceHash = sourceHash,
            Notes = "Seed demo 6A"
        });
    }

    private static async Task<MacroFeatureDefinition> EnsureFeatureDefinitionAsync(
        FinanceDbContext dbContext,
        MacroFeatureSetVersion featureSet,
        string code,
        string name,
        string dimension,
        string formula,
        decimal weight,
        int lookbackMonths,
        bool isHigherRiskOn,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.MacroFeatureDefinitions.FirstOrDefaultAsync(x => x.Code == code, cancellationToken);
        if (existing is not null)
        {
            return existing;
        }

        return dbContext.MacroFeatureDefinitions.Add(new MacroFeatureDefinition
        {
            MacroFeatureSetVersion = featureSet,
            Code = code,
            Name = name,
            Dimension = dimension,
            Formula = formula,
            Weight = weight,
            LookbackMonths = lookbackMonths,
            IsHigherRiskOn = isHigherRiskOn,
            IsActive = true
        }).Entity;
    }

    private static async Task EnsureFeatureValueAsync(
        FinanceDbContext dbContext,
        MacroFeatureDefinition definition,
        DateOnly asOfDate,
        decimal rawValue,
        decimal normalizedValue,
        decimal zScore,
        decimal momentum4Weeks,
        string interpretation,
        CancellationToken cancellationToken)
    {
        if (await dbContext.MacroFeatureValues.AnyAsync(x => x.MacroFeatureDefinitionId == definition.Id && x.AsOfDate == asOfDate, cancellationToken))
        {
            return;
        }

        dbContext.MacroFeatureValues.Add(new MacroFeatureValue
        {
            MacroFeatureDefinition = definition,
            DataAsOfDate = asOfDate,
            AsOfDate = asOfDate,
            RawValue = rawValue,
            NormalizedValue = normalizedValue,
            ZScore = zScore,
            Momentum4Weeks = momentum4Weeks,
            Interpretation = interpretation
        });
    }
}
