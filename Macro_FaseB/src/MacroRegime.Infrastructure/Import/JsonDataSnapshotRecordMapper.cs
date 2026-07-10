using System.Globalization;
using MacroRegime.Domain.Common;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Import;

public static class JsonDataSnapshotRecordMapper
{
    public const int CurrentSchemaVersion = 1;

    public static DataSnapshot ToSnapshot(JsonDataSnapshotRecord record)
    {
        ArgumentNullException.ThrowIfNull(record);

        if (record.SchemaVersion != CurrentSchemaVersion)
        {
            throw new InvalidDataException($"Unsupported data snapshot schema version {record.SchemaVersion}. Expected {CurrentSchemaVersion}.");
        }

        if (record.AsOfDate == DateOnly.MinValue)
        {
            throw new InvalidDataException("Data snapshot as-of date is required.");
        }

        if (record.MacroObservations is null)
        {
            throw new InvalidDataException("Macro observations array is required.");
        }

        if (record.MarketObservations is null)
        {
            throw new InvalidDataException("Market observations array is required.");
        }

        return new DataSnapshot(
            new AsOfDate(record.AsOfDate),
            record.MacroObservations.Select(MapMacroObservation).ToArray(),
            record.MarketObservations.Select(MapMarketObservation).ToArray());
    }

    private static MacroObservation MapMacroObservation(JsonMacroObservationRecord record)
    {
        if (record.ObservationDate == DateOnly.MinValue)
        {
            throw new InvalidDataException("Macro observation date is required.");
        }

        if (record.PublicationDate == DateOnly.MinValue)
        {
            throw new InvalidDataException("Macro publication date is required.");
        }

        return new MacroObservation(
            Require(record.SeriesCode, "Macro series code is required."),
            Require(record.Name, "Macro observation name is required."),
            ParseDimension(record.Dimension),
            new ObservationDate(record.ObservationDate),
            new PublicationDate(record.PublicationDate),
            record.VintageDate,
            record.Value,
            record.Source ?? string.Empty,
            record.Unit ?? string.Empty);
    }

    private static MarketObservation MapMarketObservation(JsonMarketObservationRecord record)
    {
        if (record.ObservationDate == DateOnly.MinValue)
        {
            throw new InvalidDataException("Market observation date is required.");
        }

        if (record.AvailabilityDate == DateOnly.MinValue)
        {
            throw new InvalidDataException("Market availability date is required.");
        }

        return new MarketObservation(
            Require(record.Symbol, "Market symbol is required."),
            Require(record.Name, "Market observation name is required."),
            ParseDimension(record.Dimension),
            new ObservationDate(record.ObservationDate),
            new AvailabilityDate(record.AvailabilityDate),
            record.Value,
            record.Source ?? string.Empty,
            record.Unit ?? string.Empty,
            record.ProxyRole ?? string.Empty);
    }

    private static EconomicDimension ParseDimension(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidDataException("Economic dimension is required.");
        }

        if (!Enum.TryParse<EconomicDimension>(value.Trim(), ignoreCase: true, out var dimension))
        {
            throw new InvalidDataException(string.Format(CultureInfo.InvariantCulture, "Economic dimension '{0}' is not supported.", value));
        }

        return dimension;
    }

    private static string Require(string? value, string message)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidDataException(message);
        }

        return value.Trim();
    }
}
