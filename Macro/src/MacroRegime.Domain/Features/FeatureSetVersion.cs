namespace MacroRegime.Domain.Features;

public sealed record FeatureSetVersion
{
    public FeatureSetVersion(string name, string version, IEnumerable<FeatureDefinition> featureDefinitions)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Feature set name is required.", nameof(name));
        }

        if (string.IsNullOrWhiteSpace(version))
        {
            throw new ArgumentException("Feature set version is required.", nameof(version));
        }

        ArgumentNullException.ThrowIfNull(featureDefinitions);

        var definitions = featureDefinitions.ToArray();
        var duplicate = definitions
            .GroupBy(definition => definition.Code, StringComparer.OrdinalIgnoreCase)
            .FirstOrDefault(group => group.Count() > 1);

        if (duplicate is not null)
        {
            throw new ArgumentException($"Feature code '{duplicate.Key}' is duplicated.", nameof(featureDefinitions));
        }

        Name = name.Trim();
        Version = version.Trim();
        FeatureDefinitions = definitions;
    }

    public string Name { get; }

    public string Version { get; }

    public IReadOnlyList<FeatureDefinition> FeatureDefinitions { get; }
}
