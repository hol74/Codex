using MacroRegime.Domain.Models;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Ports;

public interface IModelVersionProvider
{
    Task<ModelVersion?> GetActiveModelVersionAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default);
}
