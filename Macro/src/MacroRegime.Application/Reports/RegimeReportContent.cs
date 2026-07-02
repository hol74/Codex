using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Reports;

public sealed record RegimeReportContent
{
    public RegimeReportContent(RegimeSnapshot snapshot, AllocationProposal? allocationProposal = null)
    {
        Snapshot = snapshot ?? throw new ArgumentNullException(nameof(snapshot));

        if (allocationProposal is not null && allocationProposal.AsOfDate.Value != snapshot.AsOfDate.Value)
        {
            throw new ArgumentException("Allocation proposal as-of date must match regime snapshot as-of date.", nameof(allocationProposal));
        }

        AllocationProposal = allocationProposal;
    }

    public RegimeSnapshot Snapshot { get; }

    public AllocationProposal? AllocationProposal { get; }
}
