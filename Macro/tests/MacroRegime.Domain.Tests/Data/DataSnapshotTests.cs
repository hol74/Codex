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
                MacroObservation("ISM_PMI", 52m, new PublicationDate(new DateOnly(2026, 7, 1))),
                MacroObservation("ISM_PMI", 60m, new PublicationDate(new DateOnly(2026, 7, 2)))
            },
            Array.Empty<MarketObservation>());

        var found = snapshot.TryGetValue("ISM_PMI", out var value);

        Assert.True(found);
        Assert.Equal(52m, value);
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
            "Index");
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
