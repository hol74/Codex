namespace MacroRegime.Domain.Allocations;

public enum DecisionSuggestion
{
    Hold,
    WaitForConfirmation,
    PartialRebalance,
    FullRebalance,
    ManualReviewRequired
}
