using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Regimes;
using MacroRegime.Application.Regimes;

namespace MacroRegime.Application.Reports;

public sealed record GenerateRegimeReportCommand
{
    public GenerateRegimeReportCommand(
        RegimeSnapshot snapshot,
        AllocationProposal? allocationProposal = null,
        DataSnapshotSourceInfo? dataSourceInfo = null)
    {
        Content = new RegimeReportContent(snapshot, allocationProposal, dataSourceInfo);
    }

    public RegimeReportContent Content { get; }

    public RegimeSnapshot Snapshot => Content.Snapshot;

    public AllocationProposal? AllocationProposal => Content.AllocationProposal;

    public DataSnapshotSourceInfo DataSourceInfo => Content.DataSourceInfo;
}
