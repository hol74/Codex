using Microsoft.AspNetCore.DataProtection;
using Finance.Infrastructure;
using Finance.Infrastructure.Data;

var builder = WebApplication.CreateBuilder(args);

builder.Logging.ClearProviders();

var appDataDirectory = Path.Combine(builder.Environment.ContentRootPath, "App_Data");
var keyDirectory = Path.Combine(appDataDirectory, "Keys");
Directory.CreateDirectory(keyDirectory);

builder.Services.AddControllersWithViews();
builder.Services.AddDataProtection()
    .PersistKeysToFileSystem(new DirectoryInfo(keyDirectory));

var connectionString = builder.Configuration.GetConnectionString("FinanceDb")
    ?? "Data Source=App_Data/finance.sqlite";
builder.Services.AddFinanceInfrastructure(connectionString);

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var dbContext = scope.ServiceProvider.GetRequiredService<FinanceDbContext>();
    await dbContext.Database.EnsureCreatedAsync();
    await FinanceDbSeeder.EnsurePhaseSixSchemaAsync(dbContext);
    await FinanceDbSeeder.SeedAsync(dbContext);
}

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}

if (!app.Environment.IsDevelopment())
{
    app.UseHttpsRedirection();
}

app.UseRouting();

app.UseAuthorization();

app.UseStaticFiles();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();
