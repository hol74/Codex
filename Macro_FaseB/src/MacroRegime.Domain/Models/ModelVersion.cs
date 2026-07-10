namespace MacroRegime.Domain.Models;

public sealed record ModelVersion
{
    public ModelVersion(
        string name,
        string version,
        ModelRole role,
        IReadOnlyDictionary<string, decimal> parameters,
        DateOnly effectiveFrom,
        string description)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Model name is required.", nameof(name));
        }

        if (string.IsNullOrWhiteSpace(version))
        {
            throw new ArgumentException("Model version is required.", nameof(version));
        }

        if (effectiveFrom == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(effectiveFrom), "Model effective date is required.");
        }

        ArgumentNullException.ThrowIfNull(parameters);

        Name = name.Trim();
        Version = version.Trim();
        Role = role;
        Parameters = new Dictionary<string, decimal>(parameters, StringComparer.OrdinalIgnoreCase);
        EffectiveFrom = effectiveFrom;
        Description = description?.Trim() ?? string.Empty;
    }

    public string Name { get; }

    public string Version { get; }

    public ModelRole Role { get; }

    public IReadOnlyDictionary<string, decimal> Parameters { get; }

    public DateOnly EffectiveFrom { get; }

    public string Description { get; }
}
