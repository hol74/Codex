using MacroRegime.Web;
using Microsoft.AspNetCore.DataProtection;

var builder = WebApplication.CreateBuilder(args);

var dataProtectionDirectory = Path.GetFullPath(Path.Combine(builder.Environment.ContentRootPath, "../../.tmp/macro-regime-web-keys"));
Directory.CreateDirectory(dataProtectionDirectory);

builder.Logging.ClearProviders();
builder.Logging.AddConsole();

builder.Services
    .AddDataProtection()
    .PersistKeysToFileSystem(new DirectoryInfo(dataProtectionDirectory));
builder.Services.Configure<MacroRegimeWebOptions>(builder.Configuration.GetSection("MacroRegime"));
builder.Services.AddScoped<MacroRegime.Web.Services.MacroRegimeWebAnalysisService>();
builder.Services.AddRazorPages();

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
}

app.UseRouting();

app.UseAuthorization();

app.UseStaticFiles();
app.MapRazorPages();

app.Run();

public partial class Program;

