using MacroRegime.Application.Ports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Demo;

public sealed class DemoStrategicAllocationPolicyProvider : IStrategicAllocationPolicyProvider
{
    public Task<StrategicAllocationPolicy?> GetPolicyAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        return Task.FromResult<StrategicAllocationPolicy?>(DemoMacroRegimeInputs.CreateStrategicAllocationPolicy());
    }
}
