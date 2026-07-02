using MacroRegime.Application.Ports;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Demo;

public sealed class DemoFeatureSetProvider : IFeatureSetProvider
{
    public Task<FeatureSetVersion?> GetActiveFeatureSetAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        return Task.FromResult<FeatureSetVersion?>(DemoMacroRegimeInputs.CreateFeatureSetVersion());
    }
}
