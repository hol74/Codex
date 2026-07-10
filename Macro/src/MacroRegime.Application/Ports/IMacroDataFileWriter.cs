using MacroRegime.Application.External;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Ports;

public interface IMacroDataFileWriter
{
    Task<string> WriteAsync(IReadOnlyList<FredObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken cancellationToken = default);
}
