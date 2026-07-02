using MacroRegime.Domain.Allocations;

namespace MacroRegime.Application.Allocations;

public sealed record GenerateAllocationProposalResult
{
    private GenerateAllocationProposalResult(bool isSuccess, AllocationProposal? proposal, string? error)
    {
        IsSuccess = isSuccess;
        Proposal = proposal;
        Error = error;
    }

    public bool IsSuccess { get; }

    public AllocationProposal? Proposal { get; }

    public string? Error { get; }

    public static GenerateAllocationProposalResult Success(AllocationProposal proposal)
    {
        ArgumentNullException.ThrowIfNull(proposal);

        return new GenerateAllocationProposalResult(true, proposal, null);
    }

    public static GenerateAllocationProposalResult Failure(string error)
    {
        if (string.IsNullOrWhiteSpace(error))
        {
            throw new ArgumentException("Failure error is required.", nameof(error));
        }

        return new GenerateAllocationProposalResult(false, null, error.Trim());
    }
}
