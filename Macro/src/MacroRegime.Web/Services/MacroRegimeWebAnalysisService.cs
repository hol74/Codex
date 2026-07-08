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
using Microsoft.Extensions.Options;

namespace MacroRegime.Web.Services;

public sealed class MacroRegimeWebAnalysisService
{
    private readonly MacroRegimeWebOptions options;
    private readonly IWebHostEnvironment environment;

    public MacroRegimeWebAnalysisService(IOptions<MacroRegimeWebOptions> options, IWebHostEnvironment environment)
    {
        this.options = options?.Value ?? throw new ArgumentNullException(nameof(options));
        this.environment = environment ?? throw new ArgumentNullException(nameof(environment));
    }

    public async Task<WebAnalysisResult> RunAsync(DateOnly asOfDate, CancellationToken cancellationToken = default)
    {
        var configuration = GetConfiguration();
        var outputDirectory = configuration.OutputDirectory;
        var runStore = new JsonRegimeRunStore(Path.Combine(outputDirectory, "runs"));
        var manifestStore = new JsonRegimeRunManifestStore(Path.Combine(outputDirectory, "runs", "manifest.json"));
        var reportStore = new FileRegimeReportStore(Path.Combine(outputDirectory, "reports"));

        var useCase = new RunRegimeAnalysisUseCase(
            new CalculateRegimeUseCase(
                CreateDataSnapshotProvider(),
                CreateModelVersionProvider(),
                CreateFeatureSetProvider(),
                new BaselineRegimeDetector(),
                runStore),
            new GenerateAllocationProposalUseCase(
                CreateStrategicAllocationPolicyProvider(),
                CreateCurrentPortfolioProvider(),
                CreateRegimeTiltRuleProvider(),
                new AllocationProposalService()),
            new GenerateRegimeReportUseCase(new MarkdownRegimeReportRenderer(), reportStore),
            manifestStore);

        var result = await useCase
            .ExecuteAsync(new RunRegimeAnalysisCommand(asOfDate, options.EstimatedCostPerTurnover), cancellationToken)
            .ConfigureAwait(false);

        var runHistory = await manifestStore.ListAsync(cancellationToken).ConfigureAwait(false);

        return new WebAnalysisResult(
            result,
            result.RunLocation ?? runStore.GetPath(asOfDate),
            outputDirectory,
            manifestStore.FilePath,
            runHistory,
            configuration);
    }

    public WebConfigurationSummary GetConfiguration()
    {
        var outputDirectory = ResolvePath(options.OutputDirectory);
        var runDirectory = Path.Combine(outputDirectory, "runs");
        var reportDirectory = Path.Combine(outputDirectory, "reports");

        return new WebConfigurationSummary(
            options.DefaultAsOfDate,
            options.EstimatedCostPerTurnover,
            options.StrictData,
            options.StrictConfig,
            outputDirectory,
            runDirectory,
            reportDirectory,
            Path.Combine(runDirectory, "manifest.json"),
            new[]
            {
                CreateConfiguredFile("Macro data", options.DataFilePath, "Demo data", options.StrictData),
                CreateConfiguredFile("Model version", options.ModelFilePath, "Demo model", options.StrictConfig),
                CreateConfiguredFile("Feature set", options.FeatureSetFilePath, "Demo feature set", options.StrictConfig),
                CreateConfiguredFile("Allocation policy", options.PolicyFilePath, "Demo policy", options.StrictConfig),
                CreateConfiguredFile("Current portfolio", options.PortfolioFilePath, "Demo portfolio", options.StrictConfig),
                CreateConfiguredFile("Tilt rules", options.TiltsFilePath, "Demo tilt rules", options.StrictConfig)
            });
    }

    private IDataSnapshotProvider CreateDataSnapshotProvider()
    {
        var demoProvider = new DemoDataSnapshotProvider();
        return string.IsNullOrWhiteSpace(options.DataFilePath)
            ? demoProvider
            : new JsonDataSnapshotProvider(ResolvePath(options.DataFilePath), demoProvider, options.StrictData);
    }

    private IModelVersionProvider CreateModelVersionProvider()
    {
        var demoProvider = new DemoModelVersionProvider();
        return string.IsNullOrWhiteSpace(options.ModelFilePath)
            ? demoProvider
            : new JsonModelVersionProvider(ResolvePath(options.ModelFilePath), demoProvider, options.StrictConfig);
    }

    private IFeatureSetProvider CreateFeatureSetProvider()
    {
        var demoProvider = new DemoFeatureSetProvider();
        return string.IsNullOrWhiteSpace(options.FeatureSetFilePath)
            ? demoProvider
            : new JsonFeatureSetProvider(ResolvePath(options.FeatureSetFilePath), demoProvider, options.StrictConfig);
    }

    private IStrategicAllocationPolicyProvider CreateStrategicAllocationPolicyProvider()
    {
        var demoProvider = new DemoStrategicAllocationPolicyProvider();
        return string.IsNullOrWhiteSpace(options.PolicyFilePath)
            ? demoProvider
            : new JsonStrategicAllocationPolicyProvider(ResolvePath(options.PolicyFilePath), demoProvider, options.StrictConfig);
    }

    private ICurrentPortfolioProvider CreateCurrentPortfolioProvider()
    {
        var demoProvider = new DemoCurrentPortfolioProvider();
        return string.IsNullOrWhiteSpace(options.PortfolioFilePath)
            ? demoProvider
            : new JsonCurrentPortfolioProvider(ResolvePath(options.PortfolioFilePath), demoProvider, options.StrictConfig);
    }

    private IRegimeTiltRuleProvider CreateRegimeTiltRuleProvider()
    {
        var demoProvider = new DemoRegimeTiltRuleProvider();
        return string.IsNullOrWhiteSpace(options.TiltsFilePath)
            ? demoProvider
            : new JsonRegimeTiltRuleProvider(ResolvePath(options.TiltsFilePath), demoProvider, options.StrictConfig);
    }

    private string ResolvePath(string path)
    {
        return Path.GetFullPath(Path.IsPathRooted(path) ? path : Path.Combine(environment.ContentRootPath, path));
    }

    private WebConfiguredFile CreateConfiguredFile(string name, string? path, string fallbackMode, bool strict)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            return new WebConfiguredFile(name, fallbackMode, null, false, strict);
        }

        var resolvedPath = ResolvePath(path);
        return new WebConfiguredFile(name, "Local JSON", resolvedPath, File.Exists(resolvedPath), strict);
    }
}

public sealed record WebAnalysisResult(
    RunRegimeAnalysisResult Analysis,
    string RunRecordPath,
    string OutputDirectory,
    string ManifestPath,
    IReadOnlyList<RegimeRunManifestEntry> RunHistory,
    WebConfigurationSummary Configuration);

public sealed record WebConfigurationSummary(
    DateOnly DefaultAsOfDate,
    decimal EstimatedCostPerTurnover,
    bool StrictData,
    bool StrictConfig,
    string OutputDirectory,
    string RunDirectory,
    string ReportDirectory,
    string ManifestPath,
    IReadOnlyList<WebConfiguredFile> Inputs);

public sealed record WebConfiguredFile(
    string Name,
    string Mode,
    string? FilePath,
    bool Exists,
    bool Strict);
