using System.Text.Json;
using MacroRegime.Application.Import;
using MacroRegime.Application.Ports;

namespace MacroRegime.Infrastructure.Import;

public sealed class JsonImportValidationService : IImportValidationService
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    public async Task<ImportValidationReport> ValidateAsync(
        ValidateImportCommand command,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);

        var items = new List<ImportValidationItem>
        {
            await ValidateDataAsync(
                "Macro data",
                command.DataFilePath,
                command.StrictData,
                command.AsOfDate,
                cancellationToken).ConfigureAwait(false),
            await ValidateModelAsync(
                "Model version",
                command.ModelFilePath,
                command.StrictConfig,
                command.AsOfDate,
                cancellationToken).ConfigureAwait(false),
            await ValidateFeatureSetAsync(
                "Feature set",
                command.FeatureSetFilePath,
                command.StrictConfig,
                cancellationToken).ConfigureAwait(false),
            await ValidatePolicyAsync(
                "Allocation policy",
                command.PolicyFilePath,
                command.StrictConfig,
                cancellationToken).ConfigureAwait(false),
            await ValidatePortfolioAsync(
                "Current portfolio",
                command.PortfolioFilePath,
                command.StrictConfig,
                command.AsOfDate,
                cancellationToken).ConfigureAwait(false),
            await ValidateTiltsAsync(
                "Tilt rules",
                command.TiltsFilePath,
                command.StrictConfig,
                cancellationToken).ConfigureAwait(false)
        };

        return new ImportValidationReport(command.AsOfDate, items);
    }

    private static Task<ImportValidationItem> ValidateDataAsync(
        string inputKind,
        string? path,
        bool strict,
        DateOnly expectedAsOfDate,
        CancellationToken cancellationToken)
    {
        return ValidateFileAsync(
            inputKind,
            path,
            strict,
            "demo fallback used",
            async stream =>
            {
                var record = await DeserializeAsync<JsonDataSnapshotRecord>(stream, path!, cancellationToken).ConfigureAwait(false);
                var snapshot = JsonDataSnapshotRecordMapper.ToSnapshot(record);
                if (snapshot.AsOfDate.Value != expectedAsOfDate)
                {
                    throw new InvalidDataException(
                        $"Data snapshot import file '{path}' has as-of date {snapshot.AsOfDate.Value:yyyy-MM-dd}; expected {expectedAsOfDate:yyyy-MM-dd}.");
                }
            },
            cancellationToken);
    }

    private static Task<ImportValidationItem> ValidateModelAsync(
        string inputKind,
        string? path,
        bool strict,
        DateOnly expectedAsOfDate,
        CancellationToken cancellationToken)
    {
        return ValidateFileAsync(
            inputKind,
            path,
            strict,
            "demo fallback used",
            async stream =>
            {
                var record = await DeserializeAsync<JsonModelVersionRecord>(stream, path!, cancellationToken).ConfigureAwait(false);
                var model = JsonConfigurationRecordMapper.ToModelVersion(record);
                if (model.EffectiveFrom > expectedAsOfDate)
                {
                    throw new InvalidDataException(
                        $"Model version file '{path}' is effective from {model.EffectiveFrom:yyyy-MM-dd}; expected a version effective on or before {expectedAsOfDate:yyyy-MM-dd}.");
                }
            },
            cancellationToken);
    }

    private static Task<ImportValidationItem> ValidateFeatureSetAsync(
        string inputKind,
        string? path,
        bool strict,
        CancellationToken cancellationToken)
    {
        return ValidateFileAsync(
            inputKind,
            path,
            strict,
            "demo fallback used",
            async stream =>
            {
                var record = await DeserializeAsync<JsonFeatureSetVersionRecord>(stream, path!, cancellationToken).ConfigureAwait(false);
                _ = JsonConfigurationRecordMapper.ToFeatureSetVersion(record);
            },
            cancellationToken);
    }

    private static Task<ImportValidationItem> ValidatePolicyAsync(
        string inputKind,
        string? path,
        bool strict,
        CancellationToken cancellationToken)
    {
        return ValidateFileAsync(
            inputKind,
            path,
            strict,
            "demo fallback used",
            async stream =>
            {
                var record = await DeserializeAsync<JsonStrategicAllocationPolicyRecord>(stream, path!, cancellationToken).ConfigureAwait(false);
                _ = JsonConfigurationRecordMapper.ToStrategicAllocationPolicy(record);
            },
            cancellationToken);
    }

    private static Task<ImportValidationItem> ValidatePortfolioAsync(
        string inputKind,
        string? path,
        bool strict,
        DateOnly expectedAsOfDate,
        CancellationToken cancellationToken)
    {
        return ValidateFileAsync(
            inputKind,
            path,
            strict,
            "demo fallback used",
            async stream =>
            {
                var record = await DeserializeAsync<JsonCurrentPortfolioRecord>(stream, path!, cancellationToken).ConfigureAwait(false);
                _ = JsonConfigurationRecordMapper.ToCurrentPortfolio(record);
                if (record.AsOfDate != expectedAsOfDate)
                {
                    throw new InvalidDataException(
                        $"Current portfolio file '{path}' has as-of date {record.AsOfDate:yyyy-MM-dd}; expected {expectedAsOfDate:yyyy-MM-dd}.");
                }
            },
            cancellationToken);
    }

    private static Task<ImportValidationItem> ValidateTiltsAsync(
        string inputKind,
        string? path,
        bool strict,
        CancellationToken cancellationToken)
    {
        return ValidateFileAsync(
            inputKind,
            path,
            strict,
            "demo fallback used",
            async stream =>
            {
                var record = await DeserializeAsync<JsonRegimeTiltRulesRecord>(stream, path!, cancellationToken).ConfigureAwait(false);
                _ = JsonConfigurationRecordMapper.ToTiltRules(record);
            },
            cancellationToken);
    }

    private static async Task<ImportValidationItem> ValidateFileAsync(
        string inputKind,
        string? path,
        bool strict,
        string fallbackMessage,
        Func<Stream, Task> validate,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            return strict
                ? Error(inputKind, path, $"{inputKind} path is required in strict mode.")
                : Warning(inputKind, path, $"{inputKind} path is not configured; {fallbackMessage}.");
        }

        if (!File.Exists(path))
        {
            return strict
                ? Error(inputKind, path, $"{inputKind} file '{path}' does not exist.")
                : Warning(inputKind, path, $"{inputKind} file '{path}' does not exist; {fallbackMessage}.");
        }

        try
        {
            await using var stream = File.OpenRead(path);
            await validate(stream).ConfigureAwait(false);
            return Ok(inputKind, path, "Local JSON file is valid for the requested as-of date.");
        }
        catch (InvalidDataException exception)
        {
            return Error(inputKind, path, exception.Message);
        }
        catch (JsonException exception)
        {
            return Error(inputKind, path, $"{inputKind} file '{path}' is not valid JSON: {exception.Message}");
        }
        catch (IOException exception)
        {
            return Error(inputKind, path, $"{inputKind} file '{path}' could not be read: {exception.Message}");
        }
    }

    private static async Task<TRecord> DeserializeAsync<TRecord>(
        Stream stream,
        string path,
        CancellationToken cancellationToken)
    {
        var record = await JsonSerializer
            .DeserializeAsync<TRecord>(stream, SerializerOptions, cancellationToken)
            .ConfigureAwait(false);

        return record is null
            ? throw new InvalidDataException($"Import file '{path}' is empty.")
            : record;
    }

    private static ImportValidationItem Ok(string inputKind, string? path, string message)
    {
        return new ImportValidationItem(inputKind, path, ImportValidationSeverity.Ok, message);
    }

    private static ImportValidationItem Warning(string inputKind, string? path, string message)
    {
        return new ImportValidationItem(inputKind, path, ImportValidationSeverity.Warning, message);
    }

    private static ImportValidationItem Error(string inputKind, string? path, string message)
    {
        return new ImportValidationItem(inputKind, path, ImportValidationSeverity.Error, message);
    }
}
