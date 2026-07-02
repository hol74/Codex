using MacroRegime.Domain.Common;

namespace MacroRegime.Domain.Features;

public sealed record FeatureScore
{
    public FeatureScore(
        string featureCode,
        string name,
        EconomicDimension dimension,
        FeatureWeight weight,
        decimal rawValue,
        NormalizedScore normalizedScore,
        decimal? zScore,
        decimal? momentum,
        string interpretation)
    {
        if (string.IsNullOrWhiteSpace(featureCode))
        {
            throw new ArgumentException("Feature code is required.", nameof(featureCode));
        }

        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Feature score name is required.", nameof(name));
        }

        FeatureCode = featureCode.Trim();
        Name = name.Trim();
        Dimension = dimension;
        Weight = weight;
        RawValue = rawValue;
        NormalizedScore = normalizedScore;
        ZScore = zScore;
        Momentum = momentum;
        Interpretation = interpretation?.Trim() ?? string.Empty;
    }

    public string FeatureCode { get; }

    public string Name { get; }

    public EconomicDimension Dimension { get; }

    public FeatureWeight Weight { get; }

    public decimal RawValue { get; }

    public NormalizedScore NormalizedScore { get; }

    public decimal? ZScore { get; }

    public decimal? Momentum { get; }

    public string Interpretation { get; }
}
