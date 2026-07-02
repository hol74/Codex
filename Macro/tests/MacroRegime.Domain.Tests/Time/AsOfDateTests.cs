using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Tests.Time;

public sealed class AsOfDateTests
{
    [Fact]
    public void Constructor_RejectsMinValue()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new AsOfDate(DateOnly.MinValue));
    }

    [Fact]
    public void CanUse_ReturnsTrue_WhenPublicationDateIsOnOrBeforeAsOfDate()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var publicationDate = new PublicationDate(new DateOnly(2026, 6, 30));

        Assert.True(asOfDate.CanUse(publicationDate));
        Assert.True(publicationDate.IsAvailableAt(asOfDate));
    }

    [Fact]
    public void CanUse_ReturnsFalse_WhenPublicationDateIsAfterAsOfDate()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var publicationDate = new PublicationDate(new DateOnly(2026, 7, 2));

        Assert.False(asOfDate.CanUse(publicationDate));
        Assert.False(publicationDate.IsAvailableAt(asOfDate));
    }

    [Fact]
    public void CanUse_ReturnsFalse_WhenAvailabilityDateIsAfterAsOfDate()
    {
        var asOfDate = new AsOfDate(new DateOnly(2026, 7, 1));
        var availabilityDate = new AvailabilityDate(new DateOnly(2026, 7, 2));

        Assert.False(asOfDate.CanUse(availabilityDate));
        Assert.False(availabilityDate.IsAvailableAt(asOfDate));
    }
}
