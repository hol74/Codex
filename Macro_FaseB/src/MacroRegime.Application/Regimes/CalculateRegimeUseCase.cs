using MacroRegime.Application.Ports;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Regimes;

public sealed class CalculateRegimeUseCase
{
    private readonly IDataSnapshotProvider dataSnapshotProvider;
    private readonly IModelVersionProvider modelVersionProvider;
    private readonly IFeatureSetProvider featureSetProvider;
    private readonly BaselineRegimeDetector detector;

    public CalculateRegimeUseCase(
        IDataSnapshotProvider dataSnapshotProvider,
        IModelVersionProvider modelVersionProvider,
        IFeatureSetProvider featureSetProvider,
        BaselineRegimeDetector detector)
    {
        this.dataSnapshotProvider = dataSnapshotProvider ?? throw new ArgumentNullException(nameof(dataSnapshotProvider));
        this.modelVersionProvider = modelVersionProvider ?? throw new ArgumentNullException(nameof(modelVersionProvider));
        this.featureSetProvider = featureSetProvider ?? throw new ArgumentNullException(nameof(featureSetProvider));
        this.detector = detector ?? throw new ArgumentNullException(nameof(detector));
    }

    public async Task<CalculateRegimeResult> ExecuteAsync(
        CalculateRegimeCommand command,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);

        var asOfDate = new AsOfDate(command.AsOfDate);
        var modelVersion = await modelVersionProvider.GetActiveModelVersionAsync(asOfDate, cancellationToken).ConfigureAwait(false);
        if (modelVersion is null)
        {
            return CalculateRegimeResult.Failure("Model version is missing.");
        }

        var featureSetVersion = await featureSetProvider.GetActiveFeatureSetAsync(asOfDate, cancellationToken).ConfigureAwait(false);
        if (featureSetVersion is null)
        {
            return CalculateRegimeResult.Failure("Feature set version is missing.");
        }

        var dataSnapshot = await dataSnapshotProvider.GetSnapshotAsync(asOfDate, cancellationToken).ConfigureAwait(false);
        var dataSourceInfo = GetDataSourceInfo();

        if (dataSnapshot is null)
        {
            dataSnapshot = new DataSnapshot(asOfDate, Array.Empty<MacroObservation>(), Array.Empty<MarketObservation>());
            if (dataSourceInfo.Kind == DataSnapshotSourceKind.Unspecified)
            {
                dataSourceInfo = DataSnapshotSourceInfo.EmptyFallback("Provider returned no data; empty snapshot used.");
            }
        }

        var snapshot = detector.Detect(dataSnapshot, featureSetVersion, modelVersion);

        return CalculateRegimeResult.Success(snapshot, dataSourceInfo);
    }

    private DataSnapshotSourceInfo GetDataSourceInfo()
    {
        return dataSnapshotProvider is IDataSnapshotSourceInfoProvider sourceInfoProvider
            ? sourceInfoProvider.LastSourceInfo
            : DataSnapshotSourceInfo.Unspecified();
    }
}
