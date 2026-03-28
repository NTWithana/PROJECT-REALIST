using Microsoft.AspNetCore.Mvc;
using RealistAPI.Interfaces;
using RealistAPI.Models;
using RealistAPI.Services;

namespace RealistAPI.Controllers
{
    [ApiController]
    [Route("api/auth")]
    public class AuthController : ControllerBase
    {
        private readonly IUserRepository _users;
        private readonly IJwtService _jwt;
        private readonly IPasswordHasher _hasher;

        public AuthController(IUserRepository users, IJwtService jwt, IPasswordHasher hasher)
        {
            _users = users;
            _jwt = jwt;
            _hasher = hasher;
        }

        [HttpPost("register")]
        public async Task<IActionResult> Register([FromBody] RegisterRequest req)
        {
            var existing = await _users.GetByEmailAsync(req.Email);
            if (existing != null)
                return BadRequest("Email already in use.");

            var user = new User
            {
                Email = req.Email,
                DisplayName = req.DisplayName,
                PasswordHash = _hasher.Hash(req.Password)
            };

            await _users.CreateAsync(user);

            return Ok(new AuthResponse
            {
                Token = _jwt.GenerateToken(user),
                DisplayName = user.DisplayName,
                UserId = user.Id
            });
        }

        [HttpPost("login")]
        public async Task<IActionResult> Login([FromBody] LoginRequest req)
        {
            var user = await _users.GetByEmailAsync(req.Email);
            if (user == null)
                return Unauthorized("Invalid credentials.");

            if (!_hasher.Verify(req.Password, user.PasswordHash))
                return Unauthorized("Invalid credentials.");

            return Ok(new AuthResponse
            {
                Token = _jwt.GenerateToken(user),
                DisplayName = user.DisplayName,
                UserId = user.Id
            });
        }
    }
}
