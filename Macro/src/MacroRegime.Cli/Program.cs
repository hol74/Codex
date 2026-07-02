using System.Globalization;
using MacroRegime.Application.Allocations;
using MacroRegime.Application.Analysis;
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
            var dataSnapshotProvider = CreateDataSnapshotProvider(options.DataFilePath);
            var runStore = new JsonRegimeRunStore(Path.Combine(outputDirectory, "runs"));
            var reportStore = new FileRegimeReportStore(Path.Combine(outputDirectory, "reports"));

            var useCase = new RunRegimeAnalysisUseCase(
                new CalculateRegimeUseCase(
                    dataSnapshotProvider,
                    new DemoModelVersionProvider(),
                    new DemoFeatureSetProvider(),
                    new BaselineRegimeDetector(),
                    runStore),
                new GenerateAllocationProposalUseCase(
                    new DemoStrategicAllocationPolicyProvider(),
                    new DemoCurrentPortfolioProvider(),
                    new DemoRegimeTiltRuleProvider(),
                    new AllocationProposalService()),
                new GenerateRegimeReportUseCase(new MarkdownRegimeReportRenderer(), reportStore));

            var result = await useCase
                .ExecuteAsync(new RunRegimeAnalysisCommand(options.AsOfDate, options.EstimatedCostPerTurnover))
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
            Console.WriteLine($"Allocation suggestion: {result.AllocationProposal.Suggestion}");
            Console.WriteLine($"Run JSON: {runStore.GetPath(options.AsOfDate)}");
            Console.WriteLine($"Report markdown: {result.ReportLocation}");

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

    private static IDataSnapshotProvider CreateDataSnapshotProvider(string? dataFilePath)
    {
        var demoProvider = new DemoDataSnapshotProvider();
        return string.IsNullOrWhiteSpace(dataFilePath)
            ? demoProvider
            : new JsonDataSnapshotProvider(Path.GetFullPath(dataFilePath), demoProvider);
    }
}

internal sealed record CliOptions(
    DateOnly AsOfDate,
    string? DataFilePath,
    string OutputDirectory,
    decimal EstimatedCostPerTurnover,
    bool ShowHelp)
{
    public const string HelpText = """
MacroRegime.Cli

Usage:
  dotnet run --project src/MacroRegime.Cli -- --as-of yyyy-MM-dd [--data path] [--output-dir path] [--cost-per-turnover decimal]

Options:
  --as-of yyyy-MM-dd             Required analysis date.
  --data path                    Optional JSON data import file. Uses deterministic demo data as fallback.
  --output-dir path              Output directory for runs and reports. Default: macro-regime-output.
  --cost-per-turnover decimal    Estimated cost per turnover unit. Default: 0.001.
  --help                         Show help.
""";

    public static CliOptions Parse(IReadOnlyList<string> args)
    {
        if (args.Any(arg => arg is "--help" or "-h"))
        {
            return new CliOptions(DateOnly.FromDateTime(DateTime.MinValue), null, "macro-regime-output", 0.001m, true);
        }

        DateOnly? asOfDate = null;
        string? dataFilePath = null;
        var outputDirectory = "macro-regime-output";
        var estimatedCostPerTurnover = 0.001m;

        for (var index = 0; index < args.Count; index++)
        {
            var arg = args[index];
            switch (arg)
            {
                case "--as-of":
                    asOfDate = ParseDate(NextValue(args, ref index, "--as-of"), "--as-of");
                    break;
                case "--data":
                    dataFilePath = NextValue(args, ref index, "--data");
                    break;
                case "--output-dir":
                    outputDirectory = NextValue(args, ref index, "--output-dir");
                    break;
                case "--cost-per-turnover":
                    estimatedCostPerTurnover = ParseDecimal(NextValue(args, ref index, "--cost-per-turnover"), "--cost-per-turnover");
                    break;
                default:
                    throw new CliUsageException($"Unknown argument '{arg}'.");
            }
        }

        if (asOfDate is null)
        {
            throw new CliUsageException("--as-of is required.");
        }

        if (estimatedCostPerTurnover < 0m)
        {
            throw new CliUsageException("--cost-per-turnover cannot be negative.");
        }

        return new CliOptions(asOfDate.Value, dataFilePath, outputDirectory, estimatedCostPerTurnover, false);
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
