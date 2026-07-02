using MacroRegime.Domain.Common;
using MacroRegime.Domain.Explanations;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Domain.Tests.Explanations;

public sealed class RegimeExplanationBuilderTests
{
    [Fact]
    public void BuildDrivers_ReturnsDriversOrderedByImpact()
    {
        var builder = new RegimeExplanationBuilder();

        var drivers = builder.BuildDrivers(new[]
        {
            CreateScore("GROWTH_MOM", "Growth momentum", 0.7m, 1m),
            CreateScore("RISK_APPETITE", "Risk appetite", 0.9m, 2m),
            CreateScore("MONETARY_COND", "Monetary conditions", 0.4m, 3m)
        });

        Assert.Equal(new[] { "RISK_APPETITE", "MONETARY_COND", "GROWTH_MOM" }, drivers.Select(driver => driver.FeatureCode));
        Assert.All(drivers, driver => Assert.Equal(RegimeExplanationKind.Driver, driver.Kind));
    }

    [Fact]
    public void BuildContrarySignals_ReturnsRiskOffSignalsForRiskOnRegime()
    {
        var builder = new RegimeExplanationBuilder();

        var contrarySignals = builder.BuildContrarySignals(RegimeType.Goldilocks, new[]
        {
            CreateScore("GROWTH_MOM", "Growth momentum", 0.8m, 1m),
            CreateScore("CREDIT_STRESS", "Credit stress", 0.3m, 2m)
        });

        var contrarySignal = Assert.Single(contrarySignals);
        Assert.Equal("CREDIT_STRESS", contrarySignal.FeatureCode);
        Assert.Equal(RegimeExplanationKind.ContrarySignal, contrarySignal.Kind);
    }

    [Fact]
    public void BuildContrarySignals_ReturnsRiskOnSignalsForRiskOffRegime()
    {
        var builder = new RegimeExplanationBuilder();

        var contrarySignals = builder.BuildContrarySignals(RegimeType.Stagflation, new[]
        {
            CreateScore("GROWTH_MOM", "Growth momentum", 0.8m, 1m),
            CreateScore("CREDIT_STRESS", "Credit stress", 0.3m, 2m)
        });

        var contrarySignal = Assert.Single(contrarySignals);
        Assert.Equal("GROWTH_MOM", contrarySignal.FeatureCode);
        Assert.Equal(RegimeExplanationKind.ContrarySignal, contrarySignal.Kind);
    }

    [Fact]
    public void BuildContrarySignals_ReturnsEmptyListForUncertainTransition()
    {
        var builder = new RegimeExplanationBuilder();

        var contrarySignals = builder.BuildContrarySignals(RegimeType.UncertainTransition, new[]
        {
            CreateScore("GROWTH_MOM", "Growth momentum", 0.8m, 1m)
        });

        Assert.Empty(contrarySignals);
    }

    private static FeatureScore CreateScore(string code, string name, decimal normalizedScore, decimal weight)
    {
        return new FeatureScore(
            code,
            name,
            EconomicDimension.Growth,
            new FeatureWeight(weight),
            normalizedScore,
            new NormalizedScore(normalizedScore),
            null,
            null,
            string.Empty);
    }
}
