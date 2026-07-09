using System.Globalization;
using MacroRegime.Application.Allocations;
using MacroRegime.Application.Analysis;
using MacroRegime.Application.Import;
using MacroRegime.Application.Ports;
using MacroRegime.Application.Regimes;
using MacroRegime.Application.Reports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Regimes;
using MacroRegime.Infrastructure.Demo;
using MacroRegime.Infrastructure.Import;
using MacroRegime.Infrastructure.Persistence;
using MacroRegime.Infrastructure.Reporting;
using MacroRegime.Reporting.Markdown;

return await MacroRegimeCli.RunAsync(args).ConfigureAwait(false);

internal static class MacroRegimeCli
{
    public static async Task<int> RunAsync(string[] args)
    {
        try
        {
            var options = CliOptions.Parse(args);
            if (options.ShowHelp)
            {
                Console.WriteLine(CliOptions.HelpText);
                return 0;
            }

            var outputDirectory = Path.GetFullPath(options.OutputDirectory);
            if (options.ValidateOnly)
            {
                var validationReport = await new JsonImportValidationService()
                    .ValidateAsync(CreateValidationCommand(options))
                    .ConfigureAwait(false);
                var validationReportPath = await SaveValidationReportAsync(options, validationReport).ConfigureAwait(false);

                Console.WriteLine("Macro-Regime import validation completed.");
                Console.WriteLine($"As-of date: {validationReport.AsOfDate:yyyy-MM-dd}");
                Console.WriteLine($"OK: {validationReport.OkCount}");
                Console.WriteLine($"Warnings: {validationReport.WarningCount}");
                Console.WriteLine($"Errors: {validationReport.ErrorCount}");
                Console.WriteLine($"Validation report: {validationReportPath}");

                return validationReport.IsSuccess ? 0 : 2;
            }

            if (options.BatchFrom is not null || options.BatchTo is not null)
            {
                return await RunBatchAsync(options, outputDirectory).ConfigureAwait(false);
            }

            var result = await RunSingleAsync(
                    options,
                    outputDirectory,
                    options.AsOfDate,
                    options.DataFilePath,
                    options.PortfolioFilePath)
                .ConfigureAwait(false);
            if (!result.IsSuccess || result.Snapshot is null || result.AllocationProposal is null)
            {
                Console.Error.WriteLine($"Macro-Regime analysis failed: {result.Error}");
                return 2;
            }

            Console.WriteLine("Macro-Regime analysis completed.");
            Console.WriteLine($"As-of date: {result.Snapshot.AsOfDate.Value:yyyy-MM-dd}");
            Console.WriteLine($"Primary regime: {result.Snapshot.PrimaryRegime}");
            Console.WriteLine($"Operational regime: {result.Snapshot.OperationalRegime}");
            Console.WriteLine($"Data source: {result.DataSourceInfo.Kind}");
            Console.WriteLine($"Allocation suggestion: {result.AllocationProposal.Suggestion}");
            Console.WriteLine($"Run JSON: {result.RunLocation ?? Path.Combine(outputDirectory, "runs", $"regime-run-{options.AsOfDate:yyyy-MM-dd}.json")}");
            Console.WriteLine($"Report markdown: {result.ReportLocation}");
            Console.WriteLine($"Run manifest: {Path.Combine(outputDirectory, "runs", "manifest.json")}");

            return 0;
        }
        catch (CliUsageException exception)
        {
            Console.Error.WriteLine(exception.Message);
            Console.Error.WriteLine();
            Console.Error.WriteLine(CliOptions.HelpText);
            return 1;
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException)
        {
            Console.Error.WriteLine($"Macro-Regime analysis failed: {exception.Message}");
            return 2;
        }
    }

    private static async Task<int> RunBatchAsync(CliOptions options, string outputDirectory)
    {
        if (options.BatchFrom is null || options.BatchTo is null)
        {
            throw new CliUsageException("--batch-from and --batch-to must be provided together.");
        }

        if (options.BatchFrom.Value > options.BatchTo.Value)
        {
            throw new CliUsageException("--batch-from must be on or before --batch-to.");
        }

        var successCount = 0;
        var failureCount = 0;
        for (var date = options.BatchFrom.Value; date <= options.BatchTo.Value; date = date.AddDays(1))
        {
            var dataPath = ResolveDatedPath(options.DataDirectory, $"macro-data-{date:yyyy-MM-dd}.json", options.DataFilePath);
            var portfolioPath = ResolveDatedPath(options.PortfolioDirectory, $"current-portfolio-{date:yyyy-MM-dd}.json", options.PortfolioFilePath);
            try
            {
                var result = await RunSingleAsync(options, outputDirectory, date, dataPath, portfolioPath).ConfigureAwait(false);
                if (!result.IsSuccess || result.Snapshot is null || result.AllocationProposal is null)
                {
                    failureCount++;
                    Console.Error.WriteLine($"Batch run failed for {date:yyyy-MM-dd}: {result.Error}");
                    continue;
                }

                successCount++;
                Console.WriteLine($"Batch run completed for {date:yyyy-MM-dd}: {result.Snapshot.PrimaryRegime}, {result.AllocationProposal.Suggestion}");
            }
            catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException)
            {
                failureCount++;
                Console.Error.WriteLine($"Batch run failed for {date:yyyy-MM-dd}: {exception.Message}");
            }
        }

        Console.WriteLine($"Batch completed. Success: {successCount}. Failed: {failureCount}.");
        Console.WriteLine($"Run manifest: {Path.Combine(outputDirectory, "runs", "manifest.json")}");
        return failureCount == 0 ? 0 : 2;
    }

    private static async Task<RunRegimeAnalysisResult> RunSingleAsync(
        CliOptions options,
        string outputDirectory,
        DateOnly asOfDate,
        string? dataFilePath,
        string? portfolioFilePath)
    {
        var dataSnapshotProvider = CreateDataSnapshotProvider(dataFilePath, options.StrictData);
        var modelVersionProvider = CreateModelVersionProvider(options.ModelFilePath, options.StrictConfig);
        var featureSetProvider = CreateFeatureSetProvider(options.FeatureSetFilePath, options.StrictConfig);
        var allocationPolicyProvider = CreateStrategicAllocationPolicyProvider(options.PolicyFilePath, options.StrictConfig);
        var currentPortfolioProvider = CreateCurrentPortfolioProvider(portfolioFilePath, options.StrictConfig);
        var tiltRuleProvider = CreateRegimeTiltRuleProvider(options.TiltsFilePath, options.StrictConfig);
        var runStore = new JsonRegimeRunStore(Path.Combine(outputDirectory, "runs"));
        var manifestStore = new JsonRegimeRunManifestStore(Path.Combine(outputDirectory, "runs", "manifest.json"));
        var reportStore = new FileRegimeReportStore(Path.Combine(outputDirectory, "reports"));

        var useCase = new RunRegimeAnalysisUseCase(
            new CalculateRegimeUseCase(
                dataSnapshotProvider,
                modelVersionProvider,
                featureSetProvider,
                new BaselineRegimeDetector()),
            new GenerateAllocationProposalUseCase(
                allocationPolicyProvider,
                currentPortfolioProvider,
                tiltRuleProvider,
                new AllocationProposalService()),
            new GenerateRegimeReportUseCase(new MarkdownRegimeReportRenderer(), reportStore),
            runStore,
            manifestStore);

        return await useCase
            .ExecuteAsync(new RunRegimeAnalysisCommand(asOfDate, options.EstimatedCostPerTurnover))
            .ConfigureAwait(false);
    }

    private static string? ResolveDatedPath(string? directory, string fileName, string? fallbackPath)
    {
        return string.IsNullOrWhiteSpace(directory)
            ? fallbackPath
            : Path.Combine(Path.GetFullPath(directory), fileName);
    }

    private static ValidateImportCommand CreateValidationCommand(CliOptions options)
    {
        return new ValidateImportCommand(
            options.AsOfDate,
            ResolveOptionalPath(options.DataFilePath),
            ResolveOptionalPath(options.ModelFilePath),
            ResolveOptionalPath(options.FeatureSetFilePath),
            ResolveOptionalPath(options.PolicyFilePath),
            ResolveOptionalPath(options.PortfolioFilePath),
            ResolveOptionalPath(options.TiltsFilePath),
            options.StrictData,
            options.StrictConfig);
    }

    private static async Task<string> SaveValidationReportAsync(CliOptions options, ImportValidationReport report)
    {
        var outputDirectory = Path.GetFullPath(options.OutputDirectory);
        var path = string.IsNullOrWhiteSpace(options.ValidationReportPath)
            ? Path.Combine(outputDirectory, "import-validation", $"import-validation-{options.AsOfDate:yyyy-MM-dd}.md")
            : Path.GetFullPath(options.ValidationReportPath);
        var directory = Path.GetDirectoryName(path);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }

        await File.WriteAllTextAsync(path, ImportValidationMarkdownRenderer.Render(report)).ConfigureAwait(false);
        return path;
    }

    private static string? ResolveOptionalPath(string? path)
    {
        return string.IsNullOrWhiteSpace(path) ? null : Path.GetFullPath(path);
    }

    private static IDataSnapshotProvider CreateDataSnapshotProvider(string? dataFilePath, bool strictData)
    {
        var demoProvider = new DemoDataSnapshotProvider();
        return string.IsNullOrWhiteSpace(dataFilePath)
            ? demoProvider
            : new JsonDataSnapshotProvider(Path.GetFullPath(dataFilePath), demoProvider, strictData);
    }

    private static IModelVersionProvider CreateModelVersionProvider(string? filePath, bool strictConfig)
    {
        var demoProvider = new DemoModelVersionProvider();
        return string.IsNullOrWhiteSpace(filePath)
            ? demoProvider
            : new JsonModelVersionProvider(Path.GetFullPath(filePath), demoProvider, strictConfig);
    }

    private static IFeatureSetProvider CreateFeatureSetProvider(string? filePath, bool strictConfig)
    {
        var demoProvider = new DemoFeatureSetProvider();
        return string.IsNullOrWhiteSpace(filePath)
            ? demoProvider
            : new JsonFeatureSetProvider(Path.GetFullPath(filePath), demoProvider, strictConfig);
    }

    private static IStrategicAllocationPolicyProvider CreateStrategicAllocationPolicyProvider(string? filePath, bool strictConfig)
    {
        var demoProvider = new DemoStrategicAllocationPolicyProvider();
        return string.IsNullOrWhiteSpace(filePath)
            ? demoProvider
            : new JsonStrategicAllocationPolicyProvider(Path.GetFullPath(filePath), demoProvider, strictConfig);
    }

    private static ICurrentPortfolioProvider CreateCurrentPortfolioProvider(string? filePath, bool strictConfig)
    {
        var demoProvider = new DemoCurrentPortfolioProvider();
        return string.IsNullOrWhiteSpace(filePath)
            ? demoProvider
            : new JsonCurrentPortfolioProvider(Path.GetFullPath(filePath), demoProvider, strictConfig);
    }

    private static IRegimeTiltRuleProvider CreateRegimeTiltRuleProvider(string? filePath, bool strictConfig)
    {
        var demoProvider = new DemoRegimeTiltRuleProvider();
        return string.IsNullOrWhiteSpace(filePath)
            ? demoProvider
            : new JsonRegimeTiltRuleProvider(Path.GetFullPath(filePath), demoProvider, strictConfig);
    }
}

internal sealed record CliOptions(
    DateOnly AsOfDate,
    string? DataFilePath,
    string? ModelFilePath,
    string? FeatureSetFilePath,
    string? PolicyFilePath,
    string? PortfolioFilePath,
    string? TiltsFilePath,
    string OutputDirectory,
    decimal EstimatedCostPerTurnover,
    bool StrictData,
    bool StrictConfig,
    bool ValidateOnly,
    string? ValidationReportPath,
    DateOnly? BatchFrom,
    DateOnly? BatchTo,
    string? DataDirectory,
    string? PortfolioDirectory,
    bool ShowHelp)
{
    public const string HelpText = """
MacroRegime.Cli

Usage:
  dotnet run --project src/MacroRegime.Cli -- --as-of yyyy-MM-dd [--data path] [--model path] [--feature-set path] [--policy path] [--portfolio path] [--tilts path] [--strict-data] [--strict-config] [--output-dir path] [--cost-per-turnover decimal] [--validate-only] [--validate-report path]
  dotnet run --project src/MacroRegime.Cli -- --batch-from yyyy-MM-dd --batch-to yyyy-MM-dd [--data-dir path] [--portfolio-dir path] [other config options]

Options:
  --as-of yyyy-MM-dd             Required analysis date.
  --data path                    Optional JSON data import file. Uses deterministic demo data as fallback.
  --model path                   Optional JSON model version file. Uses deterministic demo config as fallback.
  --feature-set path             Optional JSON feature set file. Uses deterministic demo config as fallback.
  --policy path                  Optional JSON strategic allocation policy file. Uses deterministic demo config as fallback.
  --portfolio path               Optional JSON current portfolio file. Uses deterministic demo config as fallback.
  --tilts path                   Optional JSON regime tilt rules file. Uses deterministic demo config as fallback.
  --strict-data                  Fail if --data is missing, absent on disk, or has a different as-of date.
  --strict-config                Fail if a provided config file is absent or not effective for --as-of.
  --output-dir path              Output directory for runs and reports. Default: macro-regime-output.
  --cost-per-turnover decimal    Estimated cost per turnover unit. Default: 0.001.
  --validate-only                Validate import/config inputs and write a markdown report without running the pipeline.
  --validate-report path         Optional markdown validation report path.
  --batch-from yyyy-MM-dd        First as-of date for a daily batch run.
  --batch-to yyyy-MM-dd          Last as-of date for a daily batch run.
  --data-dir path                Directory containing macro-data-yyyy-MM-dd.json files for batch runs.
  --portfolio-dir path           Directory containing current-portfolio-yyyy-MM-dd.json files for batch runs.
  --help                         Show help.
""";

    public static CliOptions Parse(IReadOnlyList<string> args)
    {
        if (args.Any(arg => arg is "--help" or "-h"))
        {
            return new CliOptions(
                DateOnly.FromDateTime(DateTime.MinValue),
                null,
                null,
                null,
                null,
                null,
                null,
                "macro-regime-output",
                0.001m,
                false,
                false,
                false,
                null,
                null,
                null,
                null,
                null,
                true);
        }

        DateOnly? asOfDate = null;
        DateOnly? batchFrom = null;
        DateOnly? batchTo = null;
        string? dataFilePath = null;
        string? modelFilePath = null;
        string? featureSetFilePath = null;
        string? policyFilePath = null;
        string? portfolioFilePath = null;
        string? tiltsFilePath = null;
        string? dataDirectory = null;
        string? portfolioDirectory = null;
        var outputDirectory = "macro-regime-output";
        var estimatedCostPerTurnover = 0.001m;
        var strictData = false;
        var strictConfig = false;
        var validateOnly = false;
        string? validationReportPath = null;

        for (var index = 0; index < args.Count; index++)
        {
            var arg = args[index];
            switch (arg)
            {
                case "--as-of":
                    asOfDate = ParseDate(NextValue(args, ref index, "--as-of"), "--as-of");
                    break;
                case "--batch-from":
                    batchFrom = ParseDate(NextValue(args, ref index, "--batch-from"), "--batch-from");
                    break;
                case "--batch-to":
                    batchTo = ParseDate(NextValue(args, ref index, "--batch-to"), "--batch-to");
                    break;
                case "--data":
                    dataFilePath = NextValue(args, ref index, "--data");
                    break;
                case "--data-dir":
                    dataDirectory = NextValue(args, ref index, "--data-dir");
                    break;
                case "--model":
                    modelFilePath = NextValue(args, ref index, "--model");
                    break;
                case "--feature-set":
                    featureSetFilePath = NextValue(args, ref index, "--feature-set");
                    break;
                case "--policy":
                    policyFilePath = NextValue(args, ref index, "--policy");
                    break;
                case "--portfolio":
                    portfolioFilePath = NextValue(args, ref index, "--portfolio");
                    break;
                case "--portfolio-dir":
                    portfolioDirectory = NextValue(args, ref index, "--portfolio-dir");
                    break;
                case "--tilts":
                    tiltsFilePath = NextValue(args, ref index, "--tilts");
                    break;
                case "--output-dir":
                    outputDirectory = NextValue(args, ref index, "--output-dir");
                    break;
                case "--cost-per-turnover":
                    estimatedCostPerTurnover = ParseDecimal(NextValue(args, ref index, "--cost-per-turnover"), "--cost-per-turnover");
                    break;
                case "--strict-data":
                    strictData = true;
                    break;
                case "--strict-config":
                    strictConfig = true;
                    break;
                case "--validate-only":
                    validateOnly = true;
                    break;
                case "--validate-report":
                    validationReportPath = NextValue(args, ref index, "--validate-report");
                    break;
                default:
                    throw new CliUsageException($"Unknown argument '{arg}'.");
            }
        }

        if (asOfDate is null && (batchFrom is null || batchTo is null))
        {
            throw new CliUsageException("--as-of is required unless --batch-from and --batch-to are provided.");
        }

        if (estimatedCostPerTurnover < 0m)
        {
            throw new CliUsageException("--cost-per-turnover cannot be negative.");
        }

        if (strictData && string.IsNullOrWhiteSpace(dataFilePath) && string.IsNullOrWhiteSpace(dataDirectory))
        {
            throw new CliUsageException("--strict-data requires --data or --data-dir.");
        }

        return new CliOptions(
            asOfDate ?? batchFrom!.Value,
            dataFilePath,
            modelFilePath,
            featureSetFilePath,
            policyFilePath,
            portfolioFilePath,
            tiltsFilePath,
            outputDirectory,
            estimatedCostPerTurnover,
            strictData,
            strictConfig,
            validateOnly,
            validationReportPath,
            batchFrom,
            batchTo,
            dataDirectory,
            portfolioDirectory,
            false);
    }

    private static string NextValue(IReadOnlyList<string> args, ref int index, string optionName)
    {
        if (index + 1 >= args.Count)
        {
            throw new CliUsageException($"{optionName} requires a value.");
        }

        var value = args[++index];
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new CliUsageException($"{optionName} requires a non-empty value.");
        }

        return value;
    }

    private static DateOnly ParseDate(string value, string optionName)
    {
        if (!DateOnly.TryParseExact(value, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var date))
        {
            throw new CliUsageException($"{optionName} must use yyyy-MM-dd format.");
        }

        return date;
    }

    private static decimal ParseDecimal(string value, string optionName)
    {
        if (!decimal.TryParse(value, NumberStyles.Number, CultureInfo.InvariantCulture, out var parsed))
        {
            throw new CliUsageException($"{optionName} must be a decimal number using invariant culture.");
        }

        return parsed;
    }
}

internal sealed class CliUsageException(string message) : Exception(message);
