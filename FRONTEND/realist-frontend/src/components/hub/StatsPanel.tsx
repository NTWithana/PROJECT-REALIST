"use client";

import { useEffect, useState } from "react";
import { fetchGlobalStats } from "@/lib/api/stats";

type Stats = {
  totalProblems: number;
  totalSolutions: number;
  totalOptimized: number;
  totalApproved: number;
  totalReused: number;
  domainCounts?: Record<string, number>;
  tagCounts?: Record<string, number>;
};

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-3 text-center">
      <div className="text-lg font-semibold text-white">{value}</div>
      <div className="text-xs text-white/50">{label}</div>
    </div>
  );
}

export default function StatsPanel() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      try {
        const data = await fetchGlobalStats();
        if (isMounted) {
          setStats(data);
        }
      } catch (err) {
        if (isMounted) {
          setError("Failed to load stats.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return <div className="text-white/40 text-sm">Loading global stats…</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">{error}</div>;
  }

  if (!stats) {
    return <div className="text-white/40 text-sm">No stats available.</div>;
  }

  return (
    <div className="space-y-6">
      {/* TOP METRICS */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard label="Problems" value={stats.totalProblems} />
        <StatCard label="Solutions" value={stats.totalSolutions} />
        <StatCard label="Optimized" value={stats.totalOptimized} />
        <StatCard label="Approved" value={stats.totalApproved} />
        <StatCard label="Reused" value={stats.totalReused} />
      </div>

      {/* DOMAIN DISTRIBUTION */}
      <div>
        <h3 className="text-white/70 text-sm mb-2">Domains</h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.domainCounts ?? {}).length === 0 ? (
            <span className="text-white/40 text-xs">No domain data</span>
          ) : (
            Object.entries(stats.domainCounts ?? {}).map(([domain, count]) => (
              <span
                key={domain}
                className="px-2 py-1 bg-white/5 border border-white/10 rounded-md text-xs text-white/60"
              >
                {domain}: {count}
              </span>
            ))
          )}
        </div>
      </div>

      {/* TAG DISTRIBUTION */}
      <div>
        <h3 className="text-white/70 text-sm mb-2">Popular Tags</h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.tagCounts ?? {}).length === 0 ? (
            <span className="text-white/40 text-xs">No tag data</span>
          ) : (
            Object.entries(stats.tagCounts ?? {}).map(([tag, count]) => (
              <span
                key={tag}
                className="px-2 py-1 bg-white/5 border border-white/10 rounded-md text-xs text-white/60"
              >
                {tag}: {count}
              </span>
            ))
          )}
        </div>
      </div>
    </div>
  );
}