using MacroRegime.Domain.Common;

namespace MacroRegime.Domain.Features;

public sealed class CompositeScoreCalculator
{
    public NormalizedScore Calculate(IEnumerable<FeatureScore> featureScores)
    {
        ArgumentNullException.ThrowIfNull(featureScores);

        var scoredFeatures = featureScores.ToArray();
        var totalWeight = scoredFeatures.Sum(score => score.Weight.Value);

        if (totalWeight == 0m)
        {
            return NormalizedScore.Neutral;
        }

        var weightedScore = scoredFeatures.Sum(score => score.NormalizedScore.Value * score.Weight.Value) / totalWeight;
        return new NormalizedScore(weightedScore);
    }
}
