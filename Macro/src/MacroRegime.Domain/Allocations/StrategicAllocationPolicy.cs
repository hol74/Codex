namespace MacroRegime.Domain.Allocations;

public sealed record StrategicAllocationPolicy
{
    private const decimal WeightSumTolerance = 0.0001m;

    public StrategicAllocationPolicy(
        string name,
        IEnumerable<AllocationBand> bands,
        AllocationWeight maximumTurnover,
        decimal maximumEstimatedCost)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Policy name is required.", nameof(name));
        }

        ArgumentNullException.ThrowIfNull(bands);
        if (maximumEstimatedCost < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(maximumEstimatedCost), "Maximum estimated cost cannot be negative.");
        }

        var bandArray = bands.ToArray();
        if (bandArray.Length == 0)
        {
            throw new ArgumentException("At least one allocation band is required.", nameof(bands));
        }

        var duplicates = bandArray
            .GroupBy(band => band.AssetClass)
            .Where(group => group.Count() > 1)
            .Select(group => group.Key)
            .ToArray();

        if (duplicates.Length > 0)
        {
            throw new ArgumentException("Policy bands must contain each asset class only once.", nameof(bands));
        }

        var strategicSum = bandArray.Sum(band => band.Strategic.Value);
        if (Math.Abs(strategicSum - 1m) > WeightSumTolerance)
        {
            throw new ArgumentException("Strategic allocation weights must sum to one.", nameof(bands));
        }

        if (bandArray.Sum(band => band.Minimum.Value) > 1m || bandArray.Sum(band => band.Maximum.Value) < 1m)
        {
            throw new ArgumentException("Allocation bands must allow a portfolio that sums to one.", nameof(bands));
        }

        Name = name.Trim();
        Bands = bandArray.OrderBy(band => band.AssetClass).ToArray();
        MaximumTurnover = maximumTurnover;
        MaximumEstimatedCost = maximumEstimatedCost;
    }

    public string Name { get; }

    public IReadOnlyList<AllocationBand> Bands { get; }

    public AllocationWeight MaximumTurnover { get; }

    public decimal MaximumEstimatedCost { get; }

    public AllocationBand BandFor(AssetClass assetClass)
    {
        return Bands.FirstOrDefault(band => band.AssetClass == assetClass)
            ?? throw new ArgumentException($"Asset class {assetClass} is not part of the policy.", nameof(assetClass));
    }
}
