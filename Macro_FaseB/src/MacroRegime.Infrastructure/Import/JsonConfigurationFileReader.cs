using System.Text.Json;

namespace MacroRegime.Infrastructure.Import;

internal static class JsonConfigurationFileReader
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    public static async Task<TRecord> ReadRequiredAsync<TRecord>(string filePath, string description, CancellationToken cancellationToken)
        where TRecord : class
    {
        await using var stream = File.OpenRead(filePath);
        TRecord? record;
        try
        {
            record = await JsonSerializer
                .DeserializeAsync<TRecord>(stream, SerializerOptions, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException($"{description} file '{filePath}' is not valid JSON.", exception);
        }

        return record ?? throw new InvalidDataException($"{description} file '{filePath}' is empty.");
    }
}
