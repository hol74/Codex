using MacroRegime.Application.Ports;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Demo;

public sealed class DemoModelVersionProvider : IModelVersionProvider
{
    public Task<ModelVersion?> GetActiveModelVersionAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        return Task.FromResult<ModelVersion?>(DemoMacroRegimeInputs.CreateModelVersion());
    }
}
