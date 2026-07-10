using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Ports;

public interface IStrategicAllocationPolicyProvider
{
    Task<StrategicAllocationPolicy?> GetPolicyAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default);
}
