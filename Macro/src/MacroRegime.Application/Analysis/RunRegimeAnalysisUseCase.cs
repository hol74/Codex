using MacroRegime.Application.Allocations;
using MacroRegime.Application.Regimes;
using MacroRegime.Application.Reports;

namespace MacroRegime.Application.Analysis;

public sealed class RunRegimeAnalysisUseCase
{
    private readonly CalculateRegimeUseCase calculateRegimeUseCase;
    private readonly GenerateAllocationProposalUseCase generateAllocationProposalUseCase;
    private readonly GenerateRegimeReportUseCase generateRegimeReportUseCase;

    public RunRegimeAnalysisUseCase(
        CalculateRegimeUseCase calculateRegimeUseCase,
        GenerateAllocationProposalUseCase generateAllocationProposalUseCase,
        GenerateRegimeReportUseCase generateRegimeReportUseCase)
    {
        this.calculateRegimeUseCase = calculateRegimeUseCase ?? throw new ArgumentNullException(nameof(calculateRegimeUseCase));
        this.generateAllocationProposalUseCase = generateAllocationProposalUseCase ?? throw new ArgumentNullException(nameof(generateAllocationProposalUseCase));
        this.generateRegimeReportUseCase = generateRegimeReportUseCase ?? throw new ArgumentNullException(nameof(generateRegimeReportUseCase));
    }

    public async Task<RunRegimeAnalysisResult> ExecuteAsync(
        RunRegimeAnalysisCommand command,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);

        var regimeResult = await calculateRegimeUseCase
            .ExecuteAsync(new CalculateRegimeCommand(command.AsOfDate), cancellationToken)
            .ConfigureAwait(false);

        if (!regimeResult.IsSuccess || regimeResult.Snapshot is null)
        {
            return RunRegimeAnalysisResult.Failure(regimeResult.Error ?? "Regime calculation failed.");
        }

        var allocationResult = await generateAllocationProposalUseCase
            .ExecuteAsync(new GenerateAllocationProposalCommand(regimeResult.Snapshot, command.EstimatedCostPerTurnover), cancellationToken)
            .ConfigureAwait(false);

        if (!allocationResult.IsSuccess || allocationResult.Proposal is null)
        {
            return RunRegimeAnalysisResult.Failure(allocationResult.Error ?? "Allocation proposal generation failed.");
        }

        var reportResult = await generateRegimeReportUseCase
            .ExecuteAsync(new GenerateRegimeReportCommand(regimeResult.Snapshot, allocationResult.Proposal, regimeResult.DataSourceInfo), cancellationToken)
            .ConfigureAwait(false);

        return RunRegimeAnalysisResult.Success(
            regimeResult.Snapshot,
            allocationResult.Proposal,
            reportResult.Markdown,
            reportResult.Location,
            regimeResult.DataSourceInfo);
    }
}
