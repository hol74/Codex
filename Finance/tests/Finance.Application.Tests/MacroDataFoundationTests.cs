using Finance.Domain.Entities;
using Finance.Infrastructure.Data;
using Finance.Infrastructure.Services;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;

namespace Finance.Application.Tests;

public sealed class MacroDataFoundationTests
{
    [Fact]
    public async Task AsOfSnapshot_UsesOnlyVintageAvailableAtRequestedDate()
    {
        await using var connection = new SqliteConnection("Data Source=:memory:");
        await connection.OpenAsync();

        var options = new DbContextOptionsBuilder<FinanceDbContext>()
            .UseSqlite(connection)
            .Options;

        await using var dbContext = new FinanceDbContext(options);
        await dbContext.Database.EnsureCreatedAsync();

        var source = dbContext.MacroDataSources.Add(new MacroDataSource
        {
            Name = "FRED",
            Kind = "MacroApi",
            SupportsVintageData = true
        }).Entity;

        var series = dbContext.MacroSeries.Add(new MacroSeries
        {
            MacroDataSource = source,
            Code = "TEST",
            Name = "Test series",
            Category = "Growth",
            Frequency = "Monthly",
            RequiresVintageTracking = true
        }).Entity;

        var firstVintage = dbContext.DataVintages.Add(new DataVintage
        {
            MacroSeries = series,
            VintageDate = new DateOnly(2026, 1, 15),
            RealtimeStart = new DateOnly(2026, 1, 15),
            RealtimeEnd = new DateOnly(2026, 1, 15),
            SourceSystem = "FRED",
            IsOfficialVintage = true
        }).Entity;

        var revisedVintage = dbContext.DataVintages.Add(new DataVintage
        {
            MacroSeries = series,
            VintageDate = new DateOnly(2026, 3, 15),
            RealtimeStart = new DateOnly(2026, 3, 15),
            RealtimeEnd = new DateOnly(2026, 3, 15),
            SourceSystem = "ALFRED",
            IsOfficialVintage = true
        }).Entity;

        dbContext.MacroObservations.AddRange(
            new MacroObservation
            {
                MacroSeries = series,
                DataVintage = firstVintage,
                ObservationDate = new DateOnly(2025, 12, 31),
                PublishedDate = new DateOnly(2026, 1, 15),
                Value = 10m,
                Vintage = "2026-01-15"
            },
            new MacroObservation
            {
                MacroSeries = series,
                DataVintage = revisedVintage,
                ObservationDate = new DateOnly(2025, 12, 31),
                PublishedDate = new DateOnly(2026, 3, 15),
                Value = 12m,
                Vintage = "2026-03-15",
                IsRevised = true
            });

        await dbContext.SaveChangesAsync();

        var service = new MacroDataFoundationService(dbContext, new HttpClient());

        var februarySnapshot = await service.GetAsOfSnapshotAsync(new DateOnly(2026, 2, 1));
        var aprilSnapshot = await service.GetAsOfSnapshotAsync(new DateOnly(2026, 4, 1));

        Assert.Equal(10m, februarySnapshot.MacroObservations.Single().Value);
        Assert.Equal(new DateOnly(2026, 1, 15), februarySnapshot.MacroObservations.Single().VintageDate);
        Assert.Equal(12m, aprilSnapshot.MacroObservations.Single().Value);
        Assert.Equal(new DateOnly(2026, 3, 15), aprilSnapshot.MacroObservations.Single().VintageDate);
    }
}
