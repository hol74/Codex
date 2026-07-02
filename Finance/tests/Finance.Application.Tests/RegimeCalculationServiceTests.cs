using Finance.Domain.Entities;
using Finance.Infrastructure.Data;
using Finance.Infrastructure.Services;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;

namespace Finance.Application.Tests;

public sealed class RegimeCalculationServiceTests
{
    [Fact]
    public async Task CalculateAsync_UpsertsRegimeRunForSameAsOfDate()
    {
        await using var connection = new SqliteConnection("Data Source=:memory:");
        await connection.OpenAsync();

        var options = new DbContextOptionsBuilder<FinanceDbContext>()
            .UseSqlite(connection)
            .Options;

        await using var dbContext = new FinanceDbContext(options);
        await dbContext.Database.EnsureCreatedAsync();

        var asOfDate = new DateOnly(2026, 7, 1);
        await SeedSnapshotAsync(dbContext, asOfDate);

        var macroDataService = new MacroDataFoundationService(dbContext, new HttpClient());
        var service = new RegimeCalculationService(dbContext, macroDataService);

        var first = await service.CalculateAsync(asOfDate);
        var second = await service.CalculateAsync(asOfDate);

        Assert.Equal(first.PrimaryRegime, second.PrimaryRegime);
        Assert.Equal(1, await dbContext.RegimeRuns.CountAsync());
        Assert.Equal(5, await dbContext.MacroFeatureValues.CountAsync());
        Assert.True(await dbContext.RegimeProbabilities.CountAsync() > 0);
        Assert.Contains(await dbContext.AuditEvents.ToListAsync(), x => x.EventType == "RegimeCalculated");
    }

    private static async Task SeedSnapshotAsync(FinanceDbContext dbContext, DateOnly asOfDate)
    {
        var source = dbContext.MacroDataSources.Add(new MacroDataSource
        {
            Name = "TestSource",
            Kind = "Test",
            SupportsVintageData = true
        }).Entity;

        var growth = AddMacroSeries(dbContext, source, "ISM_PMI", "Growth");
        var inflation = AddMacroSeries(dbContext, source, "T10YIE", "Inflation");
        var risk = AddMacroSeries(dbContext, source, "VIX", "Risk");
        var monetary = AddMacroSeries(dbContext, source, "YC_10Y2Y", "Monetary");
        var credit = AddMacroSeries(dbContext, source, "HY_OAS", "Credit");

        AddMacroObservation(dbContext, growth, asOfDate, 52m);
        AddMacroObservation(dbContext, inflation, asOfDate, 2.2m);
        AddMacroObservation(dbContext, risk, asOfDate, 16m);
        AddMacroObservation(dbContext, monetary, asOfDate, 0.25m);
        AddMacroObservation(dbContext, credit, asOfDate, 340m);

        var marketSeries = dbContext.MarketSeries.Add(new MarketSeries
        {
            MacroDataSource = source,
            Symbol = "VWCE_PROXY",
            Name = "ETF proxy",
            Category = "ETF",
            Frequency = "Daily",
            IsProxy = true,
            IsHigherRiskOn = true
        }).Entity;

        dbContext.MarketObservations.Add(new MarketObservation
        {
            MarketSeries = marketSeries,
            Date = asOfDate.AddDays(-1),
            AvailableDate = asOfDate,
            Value = 100m
        });

        await dbContext.SaveChangesAsync();
    }

    private static MacroSeries AddMacroSeries(FinanceDbContext dbContext, MacroDataSource source, string code, string category)
    {
        return dbContext.MacroSeries.Add(new MacroSeries
        {
            MacroDataSource = source,
            Code = code,
            Name = code,
            Category = category,
            Frequency = "Daily",
            RequiresVintageTracking = true
        }).Entity;
    }

    private static void AddMacroObservation(FinanceDbContext dbContext, MacroSeries series, DateOnly asOfDate, decimal value)
    {
        var vintage = dbContext.DataVintages.Add(new DataVintage
        {
            MacroSeries = series,
            VintageDate = asOfDate,
            RealtimeStart = asOfDate,
            RealtimeEnd = asOfDate,
            SourceSystem = "TestSource",
            IsOfficialVintage = true
        }).Entity;

        dbContext.MacroObservations.Add(new MacroObservation
        {
            MacroSeries = series,
            DataVintage = vintage,
            ObservationDate = asOfDate.AddDays(-1),
            PublishedDate = asOfDate,
            Value = value,
            Vintage = asOfDate.ToString("yyyy-MM-dd")
        });
    }
}
