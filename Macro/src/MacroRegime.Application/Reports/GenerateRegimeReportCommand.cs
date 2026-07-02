using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Reports;

public sealed record GenerateRegimeReportCommand
{
    public GenerateRegimeReportCommand(RegimeSnapshot snapshot, AllocationProposal? allocationProposal = null)
    {
        Content = new RegimeReportContent(snapshot, allocationProposal);
    }

    public RegimeReportContent Content { get; }

    public RegimeSnapshot Snapshot => Content.Snapshot;

    public AllocationProposal? AllocationProposal => Content.AllocationProposal;
}
