using MacroRegime.Domain.Features;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Ports;

public interface IFeatureSetProvider
{
    Task<FeatureSetVersion?> GetActiveFeatureSetAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default);
}
