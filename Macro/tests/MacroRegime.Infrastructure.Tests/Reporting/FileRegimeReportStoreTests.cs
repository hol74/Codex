using MacroRegime.Infrastructure.Reporting;

namespace MacroRegime.Infrastructure.Tests.Reporting;

public sealed class FileRegimeReportStoreTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeReportStoreTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task SaveMarkdownAsync_WritesReportToDeterministicPath()
    {
        var asOfDate = new DateOnly(2026, 7, 1);
        var store = new FileRegimeReportStore(directoryPath);

        var location = await store.SaveMarkdownAsync(asOfDate, "# report");

        Assert.Equal(store.GetPath(asOfDate), location);
        Assert.True(File.Exists(location));
        Assert.Equal("# report", await File.ReadAllTextAsync(location));
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }
}
