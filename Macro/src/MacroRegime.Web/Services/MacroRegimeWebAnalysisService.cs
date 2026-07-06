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
        var outputDirectory = ResolvePath(options.OutputDirectory);
        var runStore = new JsonRegimeRunStore(Path.Combine(outputDirectory, "runs"));
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
            new GenerateRegimeReportUseCase(new MarkdownRegimeReportRenderer(), reportStore));

        var result = await useCase
            .ExecuteAsync(new RunRegimeAnalysisCommand(asOfDate, options.EstimatedCostPerTurnover), cancellationToken)
            .ConfigureAwait(false);

        return new WebAnalysisResult(result, runStore.GetPath(asOfDate), outputDirectory);
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
}

public sealed record WebAnalysisResult(
    RunRegimeAnalysisResult Analysis,
    string RunRecordPath,
    string OutputDirectory);
