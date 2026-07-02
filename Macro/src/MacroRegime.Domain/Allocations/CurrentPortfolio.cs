namespace MacroRegime.Domain.Allocations;

public sealed record CurrentPortfolio
{
    private const decimal WeightSumTolerance = 0.0001m;

    public CurrentPortfolio(IEnumerable<PortfolioWeight> weights)
    {
        ArgumentNullException.ThrowIfNull(weights);

        var weightArray = weights.ToArray();
        if (weightArray.Length == 0)
        {
            throw new ArgumentException("At least one portfolio weight is required.", nameof(weights));
        }

        var duplicates = weightArray
            .GroupBy(weight => weight.AssetClass)
            .Where(group => group.Count() > 1)
            .Select(group => group.Key)
            .ToArray();

        if (duplicates.Length > 0)
        {
            throw new ArgumentException("Portfolio weights must contain each asset class only once.", nameof(weights));
        }

        var sum = weightArray.Sum(weight => weight.Weight.Value);
        if (Math.Abs(sum - 1m) > WeightSumTolerance)
        {
            throw new ArgumentException("Portfolio weights must sum to one.", nameof(weights));
        }

        Weights = weightArray.OrderBy(weight => weight.AssetClass).ToArray();
    }

    public IReadOnlyList<PortfolioWeight> Weights { get; }

    public decimal WeightOf(AssetClass assetClass)
    {
        return Weights.FirstOrDefault(weight => weight.AssetClass == assetClass)?.Weight.Value ?? 0m;
    }
}
