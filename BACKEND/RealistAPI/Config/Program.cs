using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.IdentityModel.Tokens;
using MongoDB.Driver;
using RealistAPI.Interfaces;
using RealistAPI.Repositories;
using RealistAPI.Services;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// MongoDB settings
builder.Services.Configure<MongoDbSetget>(
    builder.Configuration.GetSection("MongoDB"));

builder.Services.AddSingleton<IMongoClient>(sp =>
{
    var conn = builder.Configuration.GetValue<string>("MongoDB:DBConnection");
    return new MongoClient(conn);
});

builder.Services.AddSingleton<IMongoDatabase>(sp =>
{
    var settings = builder.Configuration.GetSection("MongoDB").Get<MongoDbSetget>();
    var client = sp.GetRequiredService<IMongoClient>();
    return client.GetDatabase(settings.DBName);
});

// Services
builder.Services.AddScoped<IEmbeddingService, SimpleEmbeddingService>();
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IJwtService, JwtService>();
builder.Services.AddScoped<IPasswordHasher, Argon2PasswordHasher>();

// JWT
builder.Services.Configure<JwtSettings>(
    builder.Configuration.GetSection("Jwt"));

var jwtKey = builder.Configuration["Jwt:Key"];
var jwtIssuer = builder.Configuration["Jwt:Issuer"];

builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = jwtIssuer,
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey))
        };
    });

builder.Services.AddAuthorization();

// CORS
var allowedOrigins = builder.Configuration
    .GetSection("Cors__AllowedOrigins")
    .Get<string[]>() ?? Array.Empty<string>();

builder.Services.AddCors(options =>
{
    options.AddPolicy("FrontendOnly", policy =>
    {
        policy.WithOrigins(allowedOrigins)
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

// Rate Limiting
builder.Services.AddRateLimiter(options =>
{
    options.AddFixedWindowLimiter("fixed", opt =>
    {
        opt.PermitLimit = 120;
        opt.Window = TimeSpan.FromMinutes(1);
        opt.QueueProcessingOrder = System.Threading.RateLimiting.QueueProcessingOrder.OldestFirst;
        opt.QueueLimit = 0;
    });
});

// Controllers + Swagger
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Repositories
builder.Services.AddScoped<ISessionRepository, SessionRepository>();
builder.Services.AddScoped<IProblemRepository, ProblemRepository>();
builder.Services.AddScoped<ISolutionRepository, SolutionRepository>();
builder.Services.AddScoped<IGlobalKnowledgeRepository, GlobalKnowledgeRepository>();

// AI Engine
builder.Services.AddHttpClient<IAiEngineService, AiEngineService>();

var app = builder.Build();

// Swagger
app.UseSwagger();
app.UseSwaggerUI();

// Routing
app.UseRouting();

// CORS
app.UseCors("FrontendOnly");

// Auth
app.UseAuthentication();
app.UseAuthorization();

// Rate Limiting (AFTER auth, BEFORE controllers)
app.UseRateLimiter();

// Controllers with rate limiting
app.MapControllers().RequireRateLimiting("fixed");

app.Run();

// MongoDB settings class
public class MongoDbSetget
{
    public string DBConnection { get; set; }
    public string DBName { get; set; }
}
