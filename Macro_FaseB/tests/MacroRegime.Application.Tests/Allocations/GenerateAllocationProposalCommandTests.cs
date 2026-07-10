using MacroRegime.Application.Allocations;

namespace MacroRegime.Application.Tests.Allocations;

public sealed class GenerateAllocationProposalCommandTests
{
    [Fact]
    public void Constructor_RejectsNullSnapshot()
    {
        Assert.Throws<ArgumentNullException>(() => new GenerateAllocationProposalCommand(null!));
    }

    [Fact]
    public void Constructor_RejectsNegativeEstimatedCostPerTurnover()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new GenerateAllocationProposalCommand(
            AllocationProposalTestFixtures.CreateSnapshot(),
            -0.01m));
    }
}
