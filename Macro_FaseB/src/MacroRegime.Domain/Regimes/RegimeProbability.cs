using MacroRegime.Domain.Common;

namespace MacroRegime.Domain.Regimes;

public sealed record RegimeProbability
{
    public RegimeProbability(RegimeType regime, Probability probability, int rank)
    {
        if (rank <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(rank), "Regime probability rank must be greater than zero.");
        }

        Regime = regime;
        Probability = probability;
        Rank = rank;
    }

    public RegimeType Regime { get; }

    public Probability Probability { get; }

    public int Rank { get; }
}
