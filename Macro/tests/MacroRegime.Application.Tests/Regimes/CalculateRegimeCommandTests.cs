using MacroRegime.Application.Regimes;

namespace MacroRegime.Application.Tests.Regimes;

public sealed class CalculateRegimeCommandTests
{
    [Fact]
    public void Constructor_RejectsMissingAsOfDate()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new CalculateRegimeCommand(DateOnly.MinValue));
    }
}
