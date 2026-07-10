using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Allocations;

public sealed record GenerateAllocationProposalCommand
{
    public GenerateAllocationProposalCommand(RegimeSnapshot snapshot, decimal estimatedCostPerTurnover = 0.001m)
    {
        ArgumentNullException.ThrowIfNull(snapshot);

        if (estimatedCostPerTurnover < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(estimatedCostPerTurnover), "Estimated cost per turnover cannot be negative.");
        }

        Snapshot = snapshot;
        EstimatedCostPerTurnover = estimatedCostPerTurnover;
    }

    public RegimeSnapshot Snapshot { get; }

    public decimal EstimatedCostPerTurnover { get; }
}
