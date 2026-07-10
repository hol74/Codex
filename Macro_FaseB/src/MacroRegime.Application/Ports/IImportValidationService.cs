using MacroRegime.Application.Import;

namespace MacroRegime.Application.Ports;

public interface IImportValidationService
{
    Task<ImportValidationReport> ValidateAsync(
        ValidateImportCommand command,
        CancellationToken cancellationToken = default);
}
