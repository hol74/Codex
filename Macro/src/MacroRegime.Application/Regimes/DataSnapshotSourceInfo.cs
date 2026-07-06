namespace MacroRegime.Application.Regimes;

public enum DataSnapshotSourceKind
{
    Unspecified,
    Imported,
    Demo,
    DemoFallback,
    EmptyFallback
}

public sealed record DataSnapshotSourceInfo
{
    public DataSnapshotSourceInfo(DataSnapshotSourceKind kind, string description, string? reference = null)
    {
        if (string.IsNullOrWhiteSpace(description))
        {
            throw new ArgumentException("Data source description is required.", nameof(description));
        }

        Kind = kind;
        Description = description.Trim();
        Reference = string.IsNullOrWhiteSpace(reference) ? null : reference.Trim();
    }

    public DataSnapshotSourceKind Kind { get; }

    public string Description { get; }

    public string? Reference { get; }

    public static DataSnapshotSourceInfo Unspecified()
    {
        return new DataSnapshotSourceInfo(DataSnapshotSourceKind.Unspecified, "Data source was not reported.");
    }

    public static DataSnapshotSourceInfo Imported(string path)
    {
        return new DataSnapshotSourceInfo(DataSnapshotSourceKind.Imported, "Data snapshot imported from local JSON file.", path);
    }

    public static DataSnapshotSourceInfo Demo()
    {
        return new DataSnapshotSourceInfo(DataSnapshotSourceKind.Demo, "Deterministic demo data snapshot.");
    }

    public static DataSnapshotSourceInfo DemoFallback(string reason, string? reference = null)
    {
        return new DataSnapshotSourceInfo(DataSnapshotSourceKind.DemoFallback, reason, reference);
    }

    public static DataSnapshotSourceInfo EmptyFallback(string reason, string? reference = null)
    {
        return new DataSnapshotSourceInfo(DataSnapshotSourceKind.EmptyFallback, reason, reference);
    }
}
