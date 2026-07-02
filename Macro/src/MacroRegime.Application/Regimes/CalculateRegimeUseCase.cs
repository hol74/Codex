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
    private readonly IRegimeRunStore? regimeRunStore;

    public CalculateRegimeUseCase(
        IDataSnapshotProvider dataSnapshotProvider,
        IModelVersionProvider modelVersionProvider,
        IFeatureSetProvider featureSetProvider,
        BaselineRegimeDetector detector,
        IRegimeRunStore? regimeRunStore = null)
    {
        this.dataSnapshotProvider = dataSnapshotProvider ?? throw new ArgumentNullException(nameof(dataSnapshotProvider));
        this.modelVersionProvider = modelVersionProvider ?? throw new ArgumentNullException(nameof(modelVersionProvider));
        this.featureSetProvider = featureSetProvider ?? throw new ArgumentNullException(nameof(featureSetProvider));
        this.detector = detector ?? throw new ArgumentNullException(nameof(detector));
        this.regimeRunStore = regimeRunStore;
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

        var dataSnapshot = await dataSnapshotProvider.GetSnapshotAsync(asOfDate, cancellationToken).ConfigureAwait(false)
            ?? new DataSnapshot(asOfDate, Array.Empty<MacroObservation>(), Array.Empty<MarketObservation>());

        var snapshot = detector.Detect(dataSnapshot, featureSetVersion, modelVersion);
        if (regimeRunStore is not null)
        {
            await regimeRunStore.SaveAsync(snapshot, cancellationToken).ConfigureAwait(false);
        }

        return CalculateRegimeResult.Success(snapshot);
    }
}
