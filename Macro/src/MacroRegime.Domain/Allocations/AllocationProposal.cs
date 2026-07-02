using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Domain.Allocations;

public sealed record AllocationProposal
{
    private const decimal WeightSumTolerance = 0.0001m;

    public AllocationProposal(
        AsOfDate asOfDate,
        RegimeType operationalRegime,
        DecisionSuggestion suggestion,
        AllocationWeight turnover,
        decimal estimatedCost,
        IEnumerable<AllocationProposalLine> lines,
        IEnumerable<string> reasons,
        IEnumerable<string> constraintMessages)
    {
        if (asOfDate.Value == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "Proposal as-of date is required.");
        }

        ArgumentNullException.ThrowIfNull(lines);
        ArgumentNullException.ThrowIfNull(reasons);
        ArgumentNullException.ThrowIfNull(constraintMessages);

        if (estimatedCost < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(estimatedCost), "Estimated cost cannot be negative.");
        }

        var lineArray = lines.ToArray();
        if (lineArray.Length == 0)
        {
            throw new ArgumentException("At least one allocation proposal line is required.", nameof(lines));
        }

        var targetSum = lineArray.Sum(line => line.TargetWeight.Value);
        if (Math.Abs(targetSum - 1m) > WeightSumTolerance)
        {
            throw new ArgumentException("Target allocation weights must sum to one.", nameof(lines));
        }

        AsOfDate = asOfDate;
        OperationalRegime = operationalRegime;
        Suggestion = suggestion;
        Turnover = turnover;
        EstimatedCost = estimatedCost;
        Lines = lineArray.OrderBy(line => line.AssetClass).ToArray();
        Reasons = reasons.Where(reason => !string.IsNullOrWhiteSpace(reason)).Select(reason => reason.Trim()).ToArray();
        ConstraintMessages = constraintMessages.Where(message => !string.IsNullOrWhiteSpace(message)).Select(message => message.Trim()).ToArray();
    }

    public AsOfDate AsOfDate { get; }

    public RegimeType OperationalRegime { get; }

    public DecisionSuggestion Suggestion { get; }

    public AllocationWeight Turnover { get; }

    public decimal EstimatedCost { get; }

    public IReadOnlyList<AllocationProposalLine> Lines { get; }

    public IReadOnlyList<string> Reasons { get; }

    public IReadOnlyList<string> ConstraintMessages { get; }

    public AllocationProposalLine LineFor(AssetClass assetClass)
    {
        return Lines.FirstOrDefault(line => line.AssetClass == assetClass)
            ?? throw new ArgumentException($"Asset class {assetClass} is not part of the proposal.", nameof(assetClass));
    }
}
