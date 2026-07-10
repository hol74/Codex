namespace MacroRegime.Web;

public sealed class MacroRegimeWebOptions
{
    public DateOnly DefaultAsOfDate { get; set; } = new(2026, 7, 1);

    public string OutputDirectory { get; set; } = "../../.tmp/macro-regime-web";

    public decimal EstimatedCostPerTurnover { get; set; } = 0.001m;

    public bool StrictData { get; set; } = true;

    public bool StrictConfig { get; set; } = true;

    public string? DataFilePath { get; set; } = "../../samples/macro-data-2026-07-01.json";

    public string? ModelFilePath { get; set; } = "../../samples/model-version-baseline.json";

    public string? FeatureSetFilePath { get; set; } = "../../samples/feature-set-baseline.json";

    public string? PolicyFilePath { get; set; } = "../../samples/allocation-policy-balanced.json";

    public string? PortfolioFilePath { get; set; } = "../../samples/current-portfolio-2026-07-01.json";

    public string? TiltsFilePath { get; set; } = "../../samples/regime-tilt-rules.json";
}
