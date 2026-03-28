"use client";

import { useEffect, useState } from "react";
import { fetchTrending } from "@/lib/api/trending";

export default function TrendingPanel() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const data = await fetchTrending();
      setItems(data);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) {
    return <div className="text-white/40 text-sm">Loading global insights…</div>;
  }

  if (items.length === 0) {
    return <div className="text-white/40 text-sm">No trending data yet.</div>;
  }

  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div
          key={i}
          className="bg-white/5 border border-white/10 rounded-md p-3"
        >
          <div className="text-white/90 text-sm font-medium">
            {item.problem_summary}
          </div>

          <div className="text-white/50 text-xs mt-1">
            {item.solution_summary}
          </div>

          <div className="flex flex-wrap gap-2 mt-2 text-xs text-white/40">
            {item.domain && (
              <span className="px-2 py-0.5 bg-white/5 border border-white/10 rounded-md">
                {item.domain}
              </span>
            )}

            {item.tags?.map((t: string) => (
              <span
                key={t}
                className="px-2 py-0.5 bg-white/5 border border-white/10 rounded-md"
              >
                {t}
              </span>
            ))}
          </div>

          <div className="text-white/30 text-xs mt-2">
            Confidence: {item.confidence?.toFixed(2)}  
            • Approved: {item.approved}  
            • Optimized: {item.optimized}  
            • Reused: {item.reused}
          </div>
        </div>
      ))}
    </div>
  );
}
