using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Tests.Time;

public sealed class DateValueObjectTests
{
    [Fact]
    public void ObservationDate_RejectsMinValue()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new ObservationDate(DateOnly.MinValue));
    }

    [Fact]
    public void PublicationDate_RejectsMinValue()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new PublicationDate(DateOnly.MinValue));
    }

    [Fact]
    public void AvailabilityDate_RejectsMinValue()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new AvailabilityDate(DateOnly.MinValue));
    }

    [Fact]
    public void ObservationDate_IsNotAfterPublicationDate_WhenObservationComesFirst()
    {
        var observationDate = new ObservationDate(new DateOnly(2026, 6, 30));
        var publicationDate = new PublicationDate(new DateOnly(2026, 7, 1));

        Assert.True(observationDate.IsNotAfter(publicationDate));
    }

    [Fact]
    public void ObservationDate_IsAfterPublicationDate_WhenPublicationComesFirst()
    {
        var observationDate = new ObservationDate(new DateOnly(2026, 7, 2));
        var publicationDate = new PublicationDate(new DateOnly(2026, 7, 1));

        Assert.False(observationDate.IsNotAfter(publicationDate));
    }
}
