namespace MacroRegime.Domain.Explanations;

public sealed record RegimeExplanation
{
    public RegimeExplanation(
        string title,
        string detail,
        decimal impact,
        string? featureCode,
        RegimeExplanationKind kind)
    {
        if (string.IsNullOrWhiteSpace(title))
        {
            throw new ArgumentException("Explanation title is required.", nameof(title));
        }

        Title = title.Trim();
        Detail = detail?.Trim() ?? string.Empty;
        Impact = impact;
        FeatureCode = string.IsNullOrWhiteSpace(featureCode) ? null : featureCode.Trim();
        Kind = kind;
    }

    public string Title { get; }

    public string Detail { get; }

    public decimal Impact { get; }

    public string? FeatureCode { get; }

    public RegimeExplanationKind Kind { get; }
}
