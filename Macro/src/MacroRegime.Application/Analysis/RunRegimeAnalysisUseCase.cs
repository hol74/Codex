using MacroRegime.Application.Allocations;
using MacroRegime.Application.Ports;
using MacroRegime.Application.Regimes;
using MacroRegime.Application.Reports;

namespace MacroRegime.Application.Analysis;

public sealed class RunRegimeAnalysisUseCase
{
    private readonly CalculateRegimeUseCase calculateRegimeUseCase;
    private readonly GenerateAllocationProposalUseCase generateAllocationProposalUseCase;
    private readonly GenerateRegimeReportUseCase generateRegimeReportUseCase;
    private readonly IRegimeRunManifestStore? regimeRunManifestStore;

    public RunRegimeAnalysisUseCase(
        CalculateRegimeUseCase calculateRegimeUseCase,
        GenerateAllocationProposalUseCase generateAllocationProposalUseCase,
        GenerateRegimeReportUseCase generateRegimeReportUseCase,
        IRegimeRunManifestStore? regimeRunManifestStore = null)
    {
        this.calculateRegimeUseCase = calculateRegimeUseCase ?? throw new ArgumentNullException(nameof(calculateRegimeUseCase));
        this.generateAllocationProposalUseCase = generateAllocationProposalUseCase ?? throw new ArgumentNullException(nameof(generateAllocationProposalUseCase));
        this.generateRegimeReportUseCase = generateRegimeReportUseCase ?? throw new ArgumentNullException(nameof(generateRegimeReportUseCase));
        this.regimeRunManifestStore = regimeRunManifestStore;
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

        if (regimeRunManifestStore is not null && regimeResult.RunLocation is not null)
        {
            await regimeRunManifestStore
                .UpsertAsync(
                    new RegimeRunManifestEntry(
                        regimeResult.Snapshot.AsOfDate.Value,
                        regimeResult.RunLocation,
                        reportResult.Location,
                        regimeResult.DataSourceInfo.Kind.ToString(),
                        regimeResult.DataSourceInfo.Description,
                        regimeResult.DataSourceInfo.Reference,
                        regimeResult.Snapshot.ModelVersion.Name,
                        regimeResult.Snapshot.ModelVersion.Version,
                        regimeResult.Snapshot.FeatureSetVersion.Name,
                        regimeResult.Snapshot.FeatureSetVersion.Version,
                        regimeResult.Snapshot.PrimaryRegime.ToString(),
                        regimeResult.Snapshot.OperationalRegime.ToString(),
                        regimeResult.Snapshot.Confidence.Value,
                        regimeResult.Snapshot.CompositeScore.Value,
                        regimeResult.Snapshot.Status,
                        allocationResult.Proposal.Suggestion.ToString(),
                        allocationResult.Proposal.Turnover.Value,
                        allocationResult.Proposal.EstimatedCost,
                        regimeResult.Snapshot.Warnings.Count),
                    cancellationToken)
                .ConfigureAwait(false);
        }

        return RunRegimeAnalysisResult.Success(
            regimeResult.Snapshot,
            allocationResult.Proposal,
            reportResult.Markdown,
            reportResult.Location,
            regimeResult.RunLocation,
            regimeResult.DataSourceInfo);
    }
}
