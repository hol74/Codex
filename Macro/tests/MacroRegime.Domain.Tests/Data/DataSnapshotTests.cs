using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Tests.Data;

public sealed class DataSnapshotTests
{
    [Fact]
    public void TryGetValue_IgnoresMacroObservationPublishedAfterAsOfDate()
    {
        var snapshot = new DataSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            new[]
            {
                MacroObservation("INDPRO_YOY", 2m, new PublicationDate(new DateOnly(2026, 7, 1))),
                MacroObservation("INDPRO_YOY", 6m, new PublicationDate(new DateOnly(2026, 7, 2)))
            },
            Array.Empty<MarketObservation>());

        var found = snapshot.TryGetValue("INDPRO_YOY", out var value);

        Assert.True(found);
        Assert.Equal(2m, value);
    }

    [Fact]
    public void TryGetValue_IgnoresMarketObservationAvailableAfterAsOfDate()
    {
        var snapshot = new DataSnapshot(
            new AsOfDate(new DateOnly(2026, 7, 1)),
            Array.Empty<MacroObservation>(),
            new[]
            {
                MarketObservation("VIX", 18m, new AvailabilityDate(new DateOnly(2026, 7, 1))),
                MarketObservation("VIX", 40m, new AvailabilityDate(new DateOnly(2026, 7, 2)))
            });

        var found = snapshot.TryGetValue("VIX", out var value);

        Assert.True(found);
        Assert.Equal(18m, value);
    }

    private static MacroObservation MacroObservation(string code, decimal value, PublicationDate publicationDate)
    {
        return new MacroObservation(
            code,
            code,
            EconomicDimension.Growth,
            new ObservationDate(new DateOnly(2026, 6, 30)),
            publicationDate,
            publicationDate.Value,
            value,
            "Fixture",
            code == "INDPRO_YOY" ? "Percent change" : "Index");
    }

    private static MarketObservation MarketObservation(string symbol, decimal value, AvailabilityDate availabilityDate)
    {
        return new MarketObservation(
            symbol,
            symbol,
            EconomicDimension.Risk,
            new ObservationDate(new DateOnly(2026, 6, 30)),
            availabilityDate,
            value,
            "Fixture",
            "Index",
            "Risk proxy");
    }
}
