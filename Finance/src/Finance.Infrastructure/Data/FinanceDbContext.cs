using Finance.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace Finance.Infrastructure.Data;

public sealed class FinanceDbContext(DbContextOptions<FinanceDbContext> options) : DbContext(options)
{
    public DbSet<Owner> Owners => Set<Owner>();
    public DbSet<Currency> Currencies => Set<Currency>();
    public DbSet<AssetClass> AssetClasses => Set<AssetClass>();
    public DbSet<Portfolio> Portfolios => Set<Portfolio>();
    public DbSet<Account> Accounts => Set<Account>();
    public DbSet<Instrument> Instruments => Set<Instrument>();
    public DbSet<Transaction> Transactions => Set<Transaction>();
    public DbSet<CorporateAction> CorporateActions => Set<CorporateAction>();
    public DbSet<Price> Prices => Set<Price>();
    public DbSet<FxRate> FxRates => Set<FxRate>();
    public DbSet<HoldingSnapshot> HoldingSnapshots => Set<HoldingSnapshot>();
    public DbSet<CashFlow> CashFlows => Set<CashFlow>();
    public DbSet<Benchmark> Benchmarks => Set<Benchmark>();
    public DbSet<TargetAllocation> TargetAllocations => Set<TargetAllocation>();
    public DbSet<PerformanceSeries> PerformanceSeries => Set<PerformanceSeries>();
    public DbSet<DataSource> DataSources => Set<DataSource>();
    public DbSet<ImportBatch> ImportBatches => Set<ImportBatch>();
    public DbSet<MacroDataSource> MacroDataSources => Set<MacroDataSource>();
    public DbSet<MacroSeries> MacroSeries => Set<MacroSeries>();
    public DbSet<DataVintage> DataVintages => Set<DataVintage>();
    public DbSet<MacroObservation> MacroObservations => Set<MacroObservation>();
    public DbSet<ReleaseCalendar> ReleaseCalendar => Set<ReleaseCalendar>();
    public DbSet<MarketSeries> MarketSeries => Set<MarketSeries>();
    public DbSet<MarketObservation> MarketObservations => Set<MarketObservation>();
    public DbSet<MacroFeatureSetVersion> MacroFeatureSetVersions => Set<MacroFeatureSetVersion>();
    public DbSet<MacroFeatureDefinition> MacroFeatureDefinitions => Set<MacroFeatureDefinition>();
    public DbSet<MacroFeatureValue> MacroFeatureValues => Set<MacroFeatureValue>();
    public DbSet<RegimeModel> RegimeModels => Set<RegimeModel>();
    public DbSet<RegimeModelVersion> RegimeModelVersions => Set<RegimeModelVersion>();
    public DbSet<RegimeRun> RegimeRuns => Set<RegimeRun>();
    public DbSet<RegimeProbability> RegimeProbabilities => Set<RegimeProbability>();
    public DbSet<RegimeExplanation> RegimeExplanations => Set<RegimeExplanation>();
    public DbSet<RegimeReport> RegimeReports => Set<RegimeReport>();
    public DbSet<AuditEvent> AuditEvents => Set<AuditEvent>();
    public DbSet<PortfolioPolicy> PortfolioPolicies => Set<PortfolioPolicy>();
    public DbSet<RegimeObservation> RegimeObservations => Set<RegimeObservation>();
    public DbSet<RegimeSignal> RegimeSignals => Set<RegimeSignal>();
    public DbSet<AllocationProposal> AllocationProposals => Set<AllocationProposal>();
    public DbSet<RebalanceRecommendation> RebalanceRecommendations => Set<RebalanceRecommendation>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Currency>(entity =>
        {
            entity.HasIndex(x => x.Code).IsUnique();
            entity.Property(x => x.Code).HasMaxLength(3).IsRequired();
            entity.Property(x => x.Name).HasMaxLength(64).IsRequired();
        });

        modelBuilder.Entity<AssetClass>(entity =>
        {
            entity.HasIndex(x => x.Code).IsUnique();
            entity.Property(x => x.Code).HasMaxLength(32).IsRequired();
            entity.Property(x => x.Name).HasMaxLength(128).IsRequired();
            entity.HasOne(x => x.ParentAssetClass).WithMany().HasForeignKey(x => x.ParentAssetClassId);
        });

        modelBuilder.Entity<Portfolio>(entity =>
        {
            entity.Property(x => x.Name).HasMaxLength(128).IsRequired();
            entity.HasOne(x => x.Owner).WithMany(x => x.Portfolios).HasForeignKey(x => x.OwnerId);
            entity.HasOne(x => x.BaseCurrency).WithMany().HasForeignKey(x => x.BaseCurrencyId);
        });

        modelBuilder.Entity<Account>(entity =>
        {
            entity.Property(x => x.Name).HasMaxLength(128).IsRequired();
            entity.HasOne(x => x.Portfolio).WithMany(x => x.Accounts).HasForeignKey(x => x.PortfolioId);
            entity.HasOne(x => x.Currency).WithMany().HasForeignKey(x => x.CurrencyId);
        });

        modelBuilder.Entity<Instrument>(entity =>
        {
            entity.HasIndex(x => new { x.Symbol, x.Exchange }).IsUnique();
            entity.Property(x => x.Name).HasMaxLength(160).IsRequired();
            entity.Property(x => x.Symbol).HasMaxLength(32).IsRequired();
            entity.Property(x => x.Isin).HasMaxLength(12);
            entity.HasOne(x => x.Currency).WithMany().HasForeignKey(x => x.CurrencyId);
            entity.HasOne(x => x.AssetClass).WithMany().HasForeignKey(x => x.AssetClassId);
        });

        modelBuilder.Entity<Transaction>(entity =>
        {
            entity.HasIndex(x => x.BrokerTransactionId);
            entity.HasOne(x => x.Portfolio).WithMany().HasForeignKey(x => x.PortfolioId);
            entity.HasOne(x => x.Instrument).WithMany().HasForeignKey(x => x.InstrumentId);
            entity.HasOne(x => x.CashAccount).WithMany().HasForeignKey(x => x.CashAccountId).OnDelete(DeleteBehavior.Restrict);
            entity.HasOne(x => x.SecuritiesAccount).WithMany().HasForeignKey(x => x.SecuritiesAccountId).OnDelete(DeleteBehavior.Restrict);
            entity.HasOne(x => x.PriceCurrency).WithMany().HasForeignKey(x => x.PriceCurrencyId).OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<Price>(entity =>
        {
            entity.HasIndex(x => new { x.InstrumentId, x.Date }).IsUnique();
            entity.HasOne(x => x.Instrument).WithMany().HasForeignKey(x => x.InstrumentId);
            entity.HasOne(x => x.Currency).WithMany().HasForeignKey(x => x.CurrencyId).OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<FxRate>(entity =>
        {
            entity.HasIndex(x => new { x.FromCurrencyId, x.ToCurrencyId, x.Date }).IsUnique();
            entity.HasOne(x => x.FromCurrency).WithMany().HasForeignKey(x => x.FromCurrencyId).OnDelete(DeleteBehavior.Restrict);
            entity.HasOne(x => x.ToCurrency).WithMany().HasForeignKey(x => x.ToCurrencyId).OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<TargetAllocation>(entity =>
        {
            entity.HasIndex(x => new { x.PortfolioId, x.AssetClassId }).IsUnique();
            entity.HasOne(x => x.Portfolio).WithMany(x => x.TargetAllocations).HasForeignKey(x => x.PortfolioId);
            entity.HasOne(x => x.AssetClass).WithMany().HasForeignKey(x => x.AssetClassId);
        });

        modelBuilder.Entity<MacroDataSource>(entity =>
        {
            entity.HasIndex(x => x.Name).IsUnique();
            entity.Property(x => x.Name).HasMaxLength(96).IsRequired();
            entity.Property(x => x.Kind).HasMaxLength(48).IsRequired();
        });

        modelBuilder.Entity<MacroSeries>(entity =>
        {
            entity.HasIndex(x => x.Code).IsUnique();
            entity.Property(x => x.Code).HasMaxLength(48).IsRequired();
            entity.Property(x => x.Name).HasMaxLength(160).IsRequired();
            entity.Property(x => x.Category).HasMaxLength(64).IsRequired();
            entity.Property(x => x.Frequency).HasMaxLength(32).IsRequired();
            entity.HasOne(x => x.MacroDataSource).WithMany(x => x.Series).HasForeignKey(x => x.MacroDataSourceId);
        });

        modelBuilder.Entity<DataVintage>(entity =>
        {
            entity.HasIndex(x => new { x.MacroSeriesId, x.VintageDate, x.RealtimeStart, x.RealtimeEnd }).IsUnique();
            entity.Property(x => x.SourceSystem).HasMaxLength(64).IsRequired();
            entity.HasOne(x => x.MacroSeries).WithMany(x => x.Vintages).HasForeignKey(x => x.MacroSeriesId);
            entity.HasOne(x => x.ImportBatch).WithMany().HasForeignKey(x => x.ImportBatchId);
        });

        modelBuilder.Entity<MacroObservation>(entity =>
        {
            entity.HasIndex(x => new { x.MacroSeriesId, x.ObservationDate, x.Vintage }).IsUnique();
            entity.HasOne(x => x.MacroSeries).WithMany(x => x.Observations).HasForeignKey(x => x.MacroSeriesId);
            entity.HasOne(x => x.DataVintage).WithMany(x => x.Observations).HasForeignKey(x => x.DataVintageId);
        });

        modelBuilder.Entity<ReleaseCalendar>(entity =>
        {
            entity.HasIndex(x => new { x.MacroDataSourceId, x.ReleaseCode, x.ReleaseDate }).IsUnique();
            entity.Property(x => x.ReleaseCode).HasMaxLength(48).IsRequired();
            entity.Property(x => x.Name).HasMaxLength(160).IsRequired();
            entity.Property(x => x.Frequency).HasMaxLength(32).IsRequired();
            entity.Property(x => x.Status).HasMaxLength(32).IsRequired();
            entity.HasOne(x => x.MacroDataSource).WithMany(x => x.ReleaseCalendar).HasForeignKey(x => x.MacroDataSourceId);
        });

        modelBuilder.Entity<MarketSeries>(entity =>
        {
            entity.HasIndex(x => x.Symbol).IsUnique();
            entity.Property(x => x.Symbol).HasMaxLength(48).IsRequired();
            entity.Property(x => x.Name).HasMaxLength(160).IsRequired();
            entity.Property(x => x.Category).HasMaxLength(64).IsRequired();
            entity.Property(x => x.Frequency).HasMaxLength(32).IsRequired();
            entity.HasOne(x => x.MacroDataSource).WithMany(x => x.MarketSeries).HasForeignKey(x => x.MacroDataSourceId);
            entity.HasOne(x => x.Instrument).WithMany().HasForeignKey(x => x.InstrumentId);
        });

        modelBuilder.Entity<MarketObservation>(entity =>
        {
            entity.HasIndex(x => new { x.MarketSeriesId, x.Date }).IsUnique();
            entity.HasOne(x => x.MarketSeries).WithMany(x => x.Observations).HasForeignKey(x => x.MarketSeriesId);
        });

        modelBuilder.Entity<MacroFeatureSetVersion>(entity =>
        {
            entity.HasIndex(x => new { x.Name, x.Version }).IsUnique();
            entity.Property(x => x.Name).HasMaxLength(96).IsRequired();
            entity.Property(x => x.Version).HasMaxLength(32).IsRequired();
        });

        modelBuilder.Entity<MacroFeatureDefinition>(entity =>
        {
            entity.HasIndex(x => x.Code).IsUnique();
            entity.Property(x => x.Code).HasMaxLength(48).IsRequired();
            entity.Property(x => x.Name).HasMaxLength(160).IsRequired();
            entity.Property(x => x.Dimension).HasMaxLength(64).IsRequired();
            entity.HasOne(x => x.MacroFeatureSetVersion).WithMany(x => x.FeatureDefinitions).HasForeignKey(x => x.MacroFeatureSetVersionId);
        });

        modelBuilder.Entity<MacroFeatureValue>(entity =>
        {
            entity.HasIndex(x => new { x.MacroFeatureDefinitionId, x.AsOfDate }).IsUnique();
            entity.HasOne(x => x.MacroFeatureDefinition).WithMany(x => x.Values).HasForeignKey(x => x.MacroFeatureDefinitionId);
            entity.HasOne(x => x.MacroObservation).WithMany().HasForeignKey(x => x.MacroObservationId);
            entity.HasOne(x => x.MarketObservation).WithMany().HasForeignKey(x => x.MarketObservationId);
        });

        modelBuilder.Entity<RegimeModel>(entity =>
        {
            entity.HasIndex(x => x.Name).IsUnique();
            entity.Property(x => x.Name).HasMaxLength(96).IsRequired();
            entity.Property(x => x.Kind).HasMaxLength(48).IsRequired();
        });

        modelBuilder.Entity<RegimeModelVersion>(entity =>
        {
            entity.HasIndex(x => new { x.RegimeModelId, x.Version }).IsUnique();
            entity.Property(x => x.Version).HasMaxLength(32).IsRequired();
            entity.HasOne(x => x.RegimeModel).WithMany(x => x.Versions).HasForeignKey(x => x.RegimeModelId);
        });

        modelBuilder.Entity<RegimeRun>(entity =>
        {
            entity.HasIndex(x => new { x.RegimeModelVersionId, x.AsOfDate }).IsUnique();
            entity.Property(x => x.Status).HasMaxLength(48).IsRequired();
            entity.HasOne(x => x.RegimeModelVersion).WithMany(x => x.Runs).HasForeignKey(x => x.RegimeModelVersionId);
        });

        modelBuilder.Entity<RegimeProbability>(entity =>
        {
            entity.HasIndex(x => new { x.RegimeRunId, x.Regime }).IsUnique();
            entity.HasOne(x => x.RegimeRun).WithMany(x => x.Probabilities).HasForeignKey(x => x.RegimeRunId);
        });

        modelBuilder.Entity<RegimeExplanation>(entity =>
        {
            entity.HasOne(x => x.RegimeRun).WithMany(x => x.Explanations).HasForeignKey(x => x.RegimeRunId);
        });

        modelBuilder.Entity<RegimeReport>(entity =>
        {
            entity.HasIndex(x => new { x.RegimeRunId, x.ReportDate }).IsUnique();
            entity.HasOne(x => x.RegimeRun).WithMany().HasForeignKey(x => x.RegimeRunId);
        });

        modelBuilder.Entity<RegimeObservation>(entity =>
        {
            entity.HasIndex(x => x.ObservationDate).IsUnique();
        });

        modelBuilder.Entity<RegimeSignal>(entity =>
        {
            entity.HasOne(x => x.RegimeObservation).WithMany(x => x.Signals).HasForeignKey(x => x.RegimeObservationId);
        });

        modelBuilder.Entity<AllocationProposal>(entity =>
        {
            entity.HasOne(x => x.Portfolio).WithMany().HasForeignKey(x => x.PortfolioId);
            entity.HasOne(x => x.RegimeObservation).WithMany().HasForeignKey(x => x.RegimeObservationId);
        });

        modelBuilder.Entity<RebalanceRecommendation>(entity =>
        {
            entity.HasOne(x => x.AllocationProposal).WithMany(x => x.Recommendations).HasForeignKey(x => x.AllocationProposalId);
            entity.HasOne(x => x.AssetClass).WithMany().HasForeignKey(x => x.AssetClassId);
        });
    }
}
