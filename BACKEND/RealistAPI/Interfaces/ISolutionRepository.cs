using Microsoft.AspNetCore.Mvc;
using RealistAPI.Models;

namespace RealistAPI.Interfaces
{
    public interface ISolutionRepository
    {
        Task<SolutionDocument?> GetByIdAsync(string id);
        Task CreateAsync(SolutionDocument doc);
        Task UpdateAsync(SolutionDocument doc);




    }
}
