namespace MacroRegime.Domain.Allocations;

public sealed record AllocationProposalLine
{
    public AllocationProposalLine(
        AssetClass assetClass,
        AllocationWeight currentWeight,
        AllocationWeight strategicWeight,
        AllocationWeight targetWeight,
        AllocationWeight minimumWeight,
        AllocationWeight maximumWeight,
        decimal appliedTilt,
        decimal trade)
    {
        if (targetWeight.Value < minimumWeight.Value || targetWeight.Value > maximumWeight.Value)
        {
            throw new ArgumentException("Target weight must stay inside the allocation band.", nameof(targetWeight));
        }

        AssetClass = assetClass;
        CurrentWeight = currentWeight;
        StrategicWeight = strategicWeight;
        TargetWeight = targetWeight;
        MinimumWeight = minimumWeight;
        MaximumWeight = maximumWeight;
        AppliedTilt = appliedTilt;
        Trade = trade;
    }

    public AssetClass AssetClass { get; }

    public AllocationWeight CurrentWeight { get; }

    public AllocationWeight StrategicWeight { get; }

    public AllocationWeight TargetWeight { get; }

    public AllocationWeight MinimumWeight { get; }

    public AllocationWeight MaximumWeight { get; }

    public decimal AppliedTilt { get; }

    public decimal Trade { get; }
}
