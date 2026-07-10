using MacroRegime.Application.Ports;
using MacroRegime.Domain.Allocations;

namespace MacroRegime.Application.Allocations;

public sealed class GenerateAllocationProposalUseCase
{
    private readonly IStrategicAllocationPolicyProvider policyProvider;
    private readonly ICurrentPortfolioProvider portfolioProvider;
    private readonly IRegimeTiltRuleProvider tiltRuleProvider;
    private readonly AllocationProposalService proposalService;

    public GenerateAllocationProposalUseCase(
        IStrategicAllocationPolicyProvider policyProvider,
        ICurrentPortfolioProvider portfolioProvider,
        IRegimeTiltRuleProvider tiltRuleProvider,
        AllocationProposalService proposalService)
    {
        this.policyProvider = policyProvider ?? throw new ArgumentNullException(nameof(policyProvider));
        this.portfolioProvider = portfolioProvider ?? throw new ArgumentNullException(nameof(portfolioProvider));
        this.tiltRuleProvider = tiltRuleProvider ?? throw new ArgumentNullException(nameof(tiltRuleProvider));
        this.proposalService = proposalService ?? throw new ArgumentNullException(nameof(proposalService));
    }

    public async Task<GenerateAllocationProposalResult> ExecuteAsync(
        GenerateAllocationProposalCommand command,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);

        var asOfDate = command.Snapshot.AsOfDate;
        var policy = await policyProvider.GetPolicyAsync(asOfDate, cancellationToken).ConfigureAwait(false);
        if (policy is null)
        {
            return GenerateAllocationProposalResult.Failure("Strategic allocation policy is missing.");
        }

        var portfolio = await portfolioProvider.GetCurrentPortfolioAsync(asOfDate, cancellationToken).ConfigureAwait(false);
        if (portfolio is null)
        {
            return GenerateAllocationProposalResult.Failure("Current portfolio is missing.");
        }

        var tiltRules = await tiltRuleProvider.GetTiltRulesAsync(asOfDate, cancellationToken).ConfigureAwait(false);
        var proposal = proposalService.Propose(
            command.Snapshot,
            policy,
            portfolio,
            tiltRules,
            command.EstimatedCostPerTurnover);

        return GenerateAllocationProposalResult.Success(proposal);
    }
}
