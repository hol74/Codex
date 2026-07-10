using System.Globalization;
using MacroRegime.Application.Allocations;
using MacroRegime.Application.Analysis;
using MacroRegime.Application.External;
using MacroRegime.Application.Import;
using MacroRegime.Application.Ports;
using MacroRegime.Application.Regimes;
using MacroRegime.Application.Reports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Regimes;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.Demo;
using MacroRegime.Infrastructure.External;
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
            if (options.BuildHistoricalDataset)
            {
                return await RunBuildHistoricalDatasetAsync(options, outputDirectory).ConfigureAwait(false);
            }

            if (options.DownloadMarketData)
            {
                return await RunDownloadMarketDataAsync(options, outputDirectory).ConfigureAwait(false);
            }

            if (options.DownloadFred)
            {
                return await RunDownloadFredAsync(options, outputDirectory).ConfigureAwait(false);
            }

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

    private static async Task<int> RunBuildHistoricalDatasetAsync(CliOptions options, string outputDirectory)
    {
        var builder = new HistoricalDatasetBuilder();
        try
        {
            var result = await builder
                .BuildAsync(new BuildHistoricalDatasetCommand(
                    options.DatasetFrom!.Value,
                    options.DatasetTo!.Value,
                    Path.GetFullPath(options.MacroDataDirectory!),
                    Path.GetFullPath(options.MarketDataDirectory!),
                    outputDirectory,
                    options.ForwardReturnHorizonsDays))
                .ConfigureAwait(false);

            Console.WriteLine("Macro-Regime historical dataset build completed.");
            Console.WriteLine($"From: {options.DatasetFrom:yyyy-MM-dd}");
            Console.WriteLine($"To: {options.DatasetTo:yyyy-MM-dd}");
            Console.WriteLine($"Rows: {result.RowCount}");
            Console.WriteLine($"Skipped dates: {result.SkippedDateCount}");
            Console.WriteLine($"Forward returns: {result.ForwardReturnCount}");
            Console.WriteLine($"Historical dataset file: {result.OutputPath}");
            return 0;
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException or ArgumentException)
        {
            Console.Error.WriteLine($"Macro-Regime historical dataset build failed: {exception.Message}");
            return 2;
        }
    }

    private static async Task<int> RunDownloadMarketDataAsync(CliOptions options, string outputDirectory)
    {
        var downloadOutputDir = Path.GetFullPath(outputDirectory);
        var source = CreateMarketDataSource(options);
        var writer = new JsonMarketDataFileWriter();
        var useCase = new DownloadMarketDataUseCase(source, writer);
        try
        {
            var result = await useCase
                .ExecuteAsync(new DownloadMarketDataCommand(new AsOfDate(options.AsOfDate), MarketDataSeriesSet.Baseline, downloadOutputDir))
                .ConfigureAwait(false);
            Console.WriteLine($"Macro-Regime market data download completed ({options.MarketSource}).");
            Console.WriteLine($"As-of date: {options.AsOfDate:yyyy-MM-dd}");
            Console.WriteLine($"Series: {result.SeriesCount}");
            Console.WriteLine($"Observations: {result.ObservationCount}");
            Console.WriteLine($"Market data file: {result.OutputPath}");
            return 0;
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException or KeyNotFoundException or HttpRequestException or TaskCanceledException)
        {
            Console.Error.WriteLine($"Macro-Regime market data download failed: {exception.Message}");
            return 2;
        }
    }

    private static async Task<int> RunDownloadFredAsync(CliOptions options, string outputDirectory)
    {
        var downloadOutputDir = Path.GetFullPath(outputDirectory);
        var source = CreateFredDataSource(options);
        var writer = new JsonMacroDataFileWriter();
        var useCase = new DownloadMacroDataUseCase(source, writer);
        try
        {
            var result = await useCase
                .ExecuteAsync(new DownloadMacroDataCommand(new AsOfDate(options.AsOfDate), FredSeriesSet.Baseline, downloadOutputDir))
                .ConfigureAwait(false);
            Console.WriteLine($"Macro-Regime FRED download completed ({options.FredSource}).");
            Console.WriteLine($"As-of date: {options.AsOfDate:yyyy-MM-dd}");
            Console.WriteLine($"Series: {result.SeriesCount}");
            Console.WriteLine($"Observations: {result.ObservationCount}");
            Console.WriteLine($"Macro data file: {result.OutputPath}");
            return 0;
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException or KeyNotFoundException or HttpRequestException or TaskCanceledException)
        {
            Console.Error.WriteLine($"Macro-Regime FRED download failed: {exception.Message}");
            return 2;
        }
    }

    private static IExternalMarketDataSource CreateMarketDataSource(CliOptions options)
    {
        if (string.Equals(options.MarketSource, "stub", StringComparison.OrdinalIgnoreCase))
        {
            return new MarketDataStubDataSource();
        }

        if (string.Equals(options.MarketSource, "yahoo", StringComparison.OrdinalIgnoreCase))
        {
            return new YahooMarketDataSource(new HttpClient(), new YahooMarketDataSourceOptions());
        }

        throw new CliUsageException("--market-source must be 'stub' or 'yahoo'.");
    }

    private static IExternalMacroDataSource CreateFredDataSource(CliOptions options)
    {
        if (string.Equals(options.FredSource, "stub", StringComparison.OrdinalIgnoreCase))
        {
            return new FredStubMacroDataSource();
        }

        if (string.Equals(options.FredSource, "http", StringComparison.OrdinalIgnoreCase))
        {
            var apiKey = string.IsNullOrWhiteSpace(options.FredApiKey)
                ? ResolveFredApiKey()
                : options.FredApiKey;
            if (string.IsNullOrWhiteSpace(apiKey))
            {
                throw new CliUsageException("--fred-source http requires --fred-api-key, FRED_API_KEY, or FRED_API_KEY in .env.");
            }

            return new FredHttpMacroDataSource(new HttpClient(), new FredHttpMacroDataSourceOptions(apiKey));
        }

        throw new CliUsageException("--fred-source must be 'stub' or 'http'.");
    }

    private static string? ResolveFredApiKey()
    {
        var environmentValue = Environment.GetEnvironmentVariable("FRED_API_KEY");
        if (!string.IsNullOrWhiteSpace(environmentValue))
        {
            return environmentValue;
        }

        var envFilePath = Path.Combine(Directory.GetCurrentDirectory(), ".env");
        if (!File.Exists(envFilePath))
        {
            return null;
        }

        foreach (var line in File.ReadLines(envFilePath))
        {
            var trimmed = line.Trim();
            if (trimmed.Length == 0 || trimmed.StartsWith('#'))
            {
                continue;
            }

            var separatorIndex = trimmed.IndexOf('=');
            if (separatorIndex <= 0)
            {
                continue;
            }

            var key = trimmed[..separatorIndex].Trim();
            if (!string.Equals(key, "FRED_API_KEY", StringComparison.Ordinal))
            {
                continue;
            }

            var value = trimmed[(separatorIndex + 1)..].Trim().Trim('"');
            return string.IsNullOrWhiteSpace(value) ? null : value;
        }

        return null;
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
    bool DownloadFred,
    string FredSource,
    string? FredApiKey,
    bool DownloadMarketData,
    string MarketSource,
    bool BuildHistoricalDataset,
    DateOnly? DatasetFrom,
    DateOnly? DatasetTo,
    string? MacroDataDirectory,
    string? MarketDataDirectory,
    IReadOnlyList<int> ForwardReturnHorizonsDays,
    bool ShowHelp)
{
    public const string HelpText = """
MacroRegime.Cli

Usage:
  dotnet run --project src/MacroRegime.Cli -- --as-of yyyy-MM-dd [--data path] [--model path] [--feature-set path] [--policy path] [--portfolio path] [--tilts path] [--strict-data] [--strict-config] [--output-dir path] [--cost-per-turnover decimal] [--validate-only] [--validate-report path]
  dotnet run --project src/MacroRegime.Cli -- --batch-from yyyy-MM-dd --batch-to yyyy-MM-dd [--data-dir path] [--portfolio-dir path] [other config options]
  dotnet run --project src/MacroRegime.Cli -- --download-fred --as-of yyyy-MM-dd [--fred-source stub|http] [--fred-api-key key] [--output-dir path]
  dotnet run --project src/MacroRegime.Cli -- --download-market-data --as-of yyyy-MM-dd [--market-source stub|yahoo] [--output-dir path]
  dotnet run --project src/MacroRegime.Cli -- --build-historical-dataset --dataset-from yyyy-MM-dd --dataset-to yyyy-MM-dd --macro-data-dir path --market-data-dir path [--forward-return-days 28,56,91] [--output-dir path]

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
  --download-fred                Download FRED macro data for --as-of and write macro-data-yyyy-MM-dd.json in --output-dir. No analysis pipeline runs.
  --fred-source stub|http        FRED downloader implementation. Default: stub.
  --fred-api-key key             API key for --fred-source http. Fallback: FRED_API_KEY environment variable, then .env.
  --download-market-data         Download market data for --as-of and write market-data-yyyy-MM-dd.json in --output-dir. No analysis pipeline runs.
  --market-source stub|yahoo     Market data downloader implementation. Default: stub. Yahoo uses an unofficial chart endpoint.
  --build-historical-dataset     Build historical-dataset-from-to.json from local macro-data and market-data files.
  --dataset-from yyyy-MM-dd      First as-of date for historical dataset build.
  --dataset-to yyyy-MM-dd        Last as-of date for historical dataset build.
  --macro-data-dir path          Directory containing macro-data-yyyy-MM-dd.json files.
  --market-data-dir path         Directory containing market-data-yyyy-MM-dd.json files.
  --forward-return-days list     Comma-separated forward return horizons in calendar days. Default: 28,56,91.
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
                false,
                "stub",
                null,
                false,
                "stub",
                false,
                null,
                null,
                null,
                null,
                new[] { 28, 56, 91 },
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
        var downloadFred = false;
        var fredSource = "stub";
        string? fredApiKey = null;
        var downloadMarketData = false;
        var marketSource = "stub";
        var buildHistoricalDataset = false;
        DateOnly? datasetFrom = null;
        DateOnly? datasetTo = null;
        string? macroDataDirectory = null;
        string? marketDataDirectory = null;
        IReadOnlyList<int> forwardReturnHorizonsDays = new[] { 28, 56, 91 };
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
                case "--download-fred":
                    downloadFred = true;
                    break;
                case "--fred-source":
                    fredSource = NextValue(args, ref index, "--fred-source");
                    break;
                case "--fred-api-key":
                    fredApiKey = NextValue(args, ref index, "--fred-api-key");
                    break;
                case "--download-market-data":
                    downloadMarketData = true;
                    break;
                case "--market-source":
                    marketSource = NextValue(args, ref index, "--market-source");
                    break;
                case "--build-historical-dataset":
                    buildHistoricalDataset = true;
                    break;
                case "--dataset-from":
                    datasetFrom = ParseDate(NextValue(args, ref index, "--dataset-from"), "--dataset-from");
                    break;
                case "--dataset-to":
                    datasetTo = ParseDate(NextValue(args, ref index, "--dataset-to"), "--dataset-to");
                    break;
                case "--macro-data-dir":
                    macroDataDirectory = NextValue(args, ref index, "--macro-data-dir");
                    break;
                case "--market-data-dir":
                    marketDataDirectory = NextValue(args, ref index, "--market-data-dir");
                    break;
                case "--forward-return-days":
                    forwardReturnHorizonsDays = ParsePositiveIntList(NextValue(args, ref index, "--forward-return-days"), "--forward-return-days");
                    break;
                default:
                    throw new CliUsageException($"Unknown argument '{arg}'.");
            }
        }

        if (asOfDate is null && (batchFrom is null || batchTo is null) && !buildHistoricalDataset)
        {
            throw new CliUsageException("--as-of is required unless --batch-from and --batch-to are provided.");
        }

        if (downloadFred && asOfDate is null)
        {
            throw new CliUsageException("--download-fred requires --as-of.");
        }

        if (downloadMarketData && asOfDate is null)
        {
            throw new CliUsageException("--download-market-data requires --as-of.");
        }

        if (downloadFred && downloadMarketData)
        {
            throw new CliUsageException("--download-fred and --download-market-data are separate offline commands; run one at a time.");
        }

        if (buildHistoricalDataset && (downloadFred || downloadMarketData || validateOnly || batchFrom is not null || batchTo is not null))
        {
            throw new CliUsageException("--build-historical-dataset is a separate offline command; run it on its own.");
        }

        if (buildHistoricalDataset)
        {
            if (datasetFrom is null || datasetTo is null)
            {
                throw new CliUsageException("--build-historical-dataset requires --dataset-from and --dataset-to.");
            }

            if (datasetFrom.Value > datasetTo.Value)
            {
                throw new CliUsageException("--dataset-from must be on or before --dataset-to.");
            }

            if (string.IsNullOrWhiteSpace(macroDataDirectory))
            {
                throw new CliUsageException("--build-historical-dataset requires --macro-data-dir.");
            }

            if (string.IsNullOrWhiteSpace(marketDataDirectory))
            {
                throw new CliUsageException("--build-historical-dataset requires --market-data-dir.");
            }
        }

        if (!string.Equals(fredSource, "stub", StringComparison.OrdinalIgnoreCase)
            && !string.Equals(fredSource, "http", StringComparison.OrdinalIgnoreCase))
        {
            throw new CliUsageException("--fred-source must be 'stub' or 'http'.");
        }

        if (!string.Equals(marketSource, "stub", StringComparison.OrdinalIgnoreCase)
            && !string.Equals(marketSource, "yahoo", StringComparison.OrdinalIgnoreCase))
        {
            throw new CliUsageException("--market-source must be 'stub' or 'yahoo'.");
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
            asOfDate ?? batchFrom ?? datasetFrom!.Value,
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
            downloadFred,
            fredSource.ToLowerInvariant(),
            fredApiKey,
            downloadMarketData,
            marketSource.ToLowerInvariant(),
            buildHistoricalDataset,
            datasetFrom,
            datasetTo,
            macroDataDirectory,
            marketDataDirectory,
            forwardReturnHorizonsDays,
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

    private static IReadOnlyList<int> ParsePositiveIntList(string value, string optionName)
    {
        var parts = value.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        if (parts.Length == 0)
        {
            throw new CliUsageException($"{optionName} must contain at least one positive integer.");
        }

        var parsed = new List<int>(parts.Length);
        foreach (var part in parts)
        {
            if (!int.TryParse(part, NumberStyles.None, CultureInfo.InvariantCulture, out var number) || number <= 0)
            {
                throw new CliUsageException($"{optionName} must contain only positive integers.");
            }

            parsed.Add(number);
        }

        return parsed;
    }
}

internal sealed class CliUsageException(string message) : Exception(message);
