using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using MongoDB.Driver;
using RealistAPI.Interfaces;
using RealistAPI.Repositories;
using RealistAPI.Services;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// Bind MongoDB settings
builder.Services.Configure<MongoDbSetget>(
    builder.Configuration.GetSection("MongoDB"));

// Register MongoClient
builder.Services.AddSingleton<IMongoClient>(sp =>
{
    var conn = builder.Configuration.GetValue<string>("MongoDB:DBConnection");
    return new MongoClient(conn);
});

// Register IMongoDatabase
builder.Services.AddSingleton<IMongoDatabase>(sp =>
{
    var settings = builder.Configuration.GetSection("MongoDB").Get<MongoDbSetget>();
    var client = sp.GetRequiredService<IMongoClient>();
    return client.GetDatabase(settings.DBName);
});

// Register embedding service
builder.Services.AddScoped<IEmbeddingService, SimpleEmbeddingService>();

// Auth services
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IJwtService, JwtService>();
builder.Services.AddScoped<IPasswordHasher, Argon2PasswordHasher>();

// JWT Authentication
builder.Services.Configure<JwtSettings>(
    builder.Configuration.GetSection("Jwt"));

var jwtKey = builder.Configuration["Jwt:Key"];
var jwtIssuer = builder.Configuration["Jwt:Issuer"];

builder.Services
    .AddAuthentication(options =>
    {
        options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
        options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
    })
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

// Controllers
builder.Services.AddControllers();

// Repositories
builder.Services.AddScoped<ISessionRepository, SessionRepository>();
builder.Services.AddScoped<IProblemRepository, ProblemRepository>();
builder.Services.AddScoped<ISolutionRepository, SolutionRepository>();
builder.Services.AddScoped<IGlobalKnowledgeRepository, GlobalKnowledgeRepository>();

// AI Engine
builder.Services.AddHttpClient<IAiEngineService, AiEngineService>();

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// cors configuration
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

var app = builder.Build();


app.UseSwagger();
app.UseSwaggerUI();


// CORS middleware 
app.UseCors("AllowAll");

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();

// MongoDB settings class
public class MongoDbSetget
{
    public string DBConnection { get; set; }
    public string DBName { get; set; }
}