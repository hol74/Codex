using MacroRegime.Application.Ports;
using MacroRegime.Application.Regimes;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Tests.Regimes;

public sealed class CalculateRegimeUseCaseTests
{
    [Fact]
    public async Task ExecuteAsync_CalculatesRegimeSnapshotFromInMemoryProviders()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var dataProvider = new FakeDataSnapshotProvider(CreateGoldilocksSnapshot(new AsOfDate(asOfDate)));
        var useCase = CreateUseCase(dataProvider, new FakeModelVersionProvider(CreateModelVersion()), new FakeFeatureSetProvider(CreateFeatureSetVersion()));

        var result = await useCase.ExecuteAsync(new CalculateRegimeCommand(asOfDate));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Snapshot);
        Assert.Equal(RegimeType.Goldilocks, result.Snapshot.PrimaryRegime);
        Assert.Equal(RegimeType.Goldilocks, result.Snapshot.OperationalRegime);
        Assert.Equal(asOfDate, dataProvider.RequestedAsOfDate?.Value);
    }

    [Fact]
    public async Task ExecuteAsync_UsesEmptySnapshot_WhenSnapshotProviderReturnsNoData()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var useCase = CreateUseCase(
            new FakeDataSnapshotProvider(null),
            new FakeModelVersionProvider(CreateModelVersion()),
            new FakeFeatureSetProvider(CreateFeatureSetVersion()));

        var result = await useCase.ExecuteAsync(new CalculateRegimeCommand(asOfDate));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Snapshot);
        Assert.Equal(RegimeType.UncertainTransition, result.Snapshot.OperationalRegime);
        Assert.NotEmpty(result.Snapshot.Warnings);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsFailure_WhenModelVersionIsMissing()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var useCase = CreateUseCase(
            new FakeDataSnapshotProvider(CreateGoldilocksSnapshot(new AsOfDate(asOfDate))),
            new FakeModelVersionProvider(null),
            new FakeFeatureSetProvider(CreateFeatureSetVersion()));

        var result = await useCase.ExecuteAsync(new CalculateRegimeCommand(asOfDate));

        Assert.False(result.IsSuccess);
        Assert.Null(result.Snapshot);
        Assert.Equal("Model version is missing.", result.Error);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsFailure_WhenFeatureSetVersionIsMissing()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var useCase = CreateUseCase(
            new FakeDataSnapshotProvider(CreateGoldilocksSnapshot(new AsOfDate(asOfDate))),
            new FakeModelVersionProvider(CreateModelVersion()),
            new FakeFeatureSetProvider(null));

        var result = await useCase.ExecuteAsync(new CalculateRegimeCommand(asOfDate));

        Assert.False(result.IsSuccess);
        Assert.Null(result.Snapshot);
        Assert.Equal("Feature set version is missing.", result.Error);
    }

    private static CalculateRegimeUseCase CreateUseCase(
        IDataSnapshotProvider dataSnapshotProvider,
        IModelVersionProvider modelVersionProvider,
        IFeatureSetProvider featureSetProvider)
    {
        return new CalculateRegimeUseCase(
            dataSnapshotProvider,
            modelVersionProvider,
            featureSetProvider,
            new BaselineRegimeDetector());
    }

    private static DataSnapshot CreateGoldilocksSnapshot(AsOfDate asOfDate)
    {
        var observationDate = new ObservationDate(new DateOnly(2026, 6, 30));
        var publicationDate = new PublicationDate(asOfDate.Value);

        return new DataSnapshot(
            asOfDate,
            new[]
            {
                Observation("INDPRO_YOY", EconomicDimension.Growth, 5m, observationDate, publicationDate),
                Observation("SAHM", EconomicDimension.Growth, 0.05m, observationDate, publicationDate),
                Observation("T10YIE", EconomicDimension.Inflation, 2.0m, observationDate, publicationDate),
                Observation("VIX", EconomicDimension.Risk, 14m, observationDate, publicationDate),
                Observation("YC_10Y2Y", EconomicDimension.Monetary, 0.5m, observationDate, publicationDate),
                Observation("HY_OAS", EconomicDimension.Credit, 3m, observationDate, publicationDate)
            },
            Array.Empty<MarketObservation>());
    }

    private static MacroObservation Observation(
        string code,
        EconomicDimension dimension,
        decimal value,
        ObservationDate observationDate,
        PublicationDate publicationDate)
    {
        return new MacroObservation(
            code,
            code,
            dimension,
            observationDate,
            publicationDate,
            publicationDate.Value,
            value,
            "Fixture",
            code == "INDPRO_YOY" ? "Percent change" : "Index");
    }

    private static FeatureSetVersion CreateFeatureSetVersion()
    {
        return new FeatureSetVersion(
            "CRS Baseline",
            "0.1",
            new[]
            {
                Feature("GROWTH_MOM", "Growth momentum", EconomicDimension.Growth, FeaturePolarity.HigherIsRiskOn),
                Feature("INFL_PRESS", "Inflation pressure", EconomicDimension.Inflation, FeaturePolarity.HigherIsRiskOff),
                Feature("RISK_APPETITE", "Risk appetite", EconomicDimension.Risk, FeaturePolarity.HigherIsRiskOn),
                Feature("MONETARY_COND", "Monetary conditions", EconomicDimension.Monetary, FeaturePolarity.HigherIsRiskOn),
                Feature("CREDIT_STRESS", "Credit stress", EconomicDimension.Credit, FeaturePolarity.HigherIsRiskOff)
            });
    }

    private static FeatureDefinition Feature(string code, string name, EconomicDimension dimension, FeaturePolarity polarity)
    {
        return new FeatureDefinition(
            code,
            name,
            dimension,
            "Baseline v0.1 formula",
            new FeatureWeight(1m),
            polarity,
            6,
            true);
    }

    private static ModelVersion CreateModelVersion()
    {
        return new ModelVersion(
            "CRS Rule-Based Engine",
            "0.1",
            ModelRole.Baseline,
            new Dictionary<string, decimal>
            {
                ["confirmation_threshold"] = 0.55m
            },
            new DateOnly(2026, 7, 1),
            "Baseline model");
    }

    private sealed class FakeDataSnapshotProvider(DataSnapshot? snapshot) : IDataSnapshotProvider
    {
        public AsOfDate? RequestedAsOfDate { get; private set; }

        public Task<DataSnapshot?> GetSnapshotAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            RequestedAsOfDate = asOfDate;
            return Task.FromResult(snapshot);
        }
    }

    private sealed class FakeModelVersionProvider(ModelVersion? modelVersion) : IModelVersionProvider
    {
        public Task<ModelVersion?> GetActiveModelVersionAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(modelVersion);
        }
    }

    private sealed class FakeFeatureSetProvider(FeatureSetVersion? featureSetVersion) : IFeatureSetProvider
    {
        public Task<FeatureSetVersion?> GetActiveFeatureSetAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(featureSetVersion);
        }
    }

}
