import { RefreshCw } from "lucide-react";
import { performanceMetrics } from "../data/mockData";

const metrics = [
  { label: "Avg. Delay / Veh",   value: performanceMetrics.avgDelay },
  { label: "Avg. Queue Length",   value: performanceMetrics.avgQueueLength },
  { label: "95th %ile Queue",     value: performanceMetrics.queue95th },
  { label: "Throughput",          value: performanceMetrics.throughput },
  { label: "Safety Index",        value: performanceMetrics.safetyIndex },
];

export default function PerformanceSnapshot() {
  return (
    <div className="bottom-card">
      <div className="bottom-card__title-row">
        <h3 className="bottom-card__title">PERFORMANCE SNAPSHOT</h3>
        <button className="bottom-card__refresh" title="Refresh">
          <RefreshCw size={13} />
        </button>
      </div>

      <div className="perf__metrics">
        {metrics.map((m) => (
          <div key={m.label} className="perf__row">
            <span className="perf__label">{m.label}</span>
            <span className="perf__value font-mono">{m.value}</span>
          </div>
        ))}
      </div>

      <div className="perf__last-run">
        <span className="perf__last-run-label">Last Run</span>
        <span className="perf__last-run-value font-mono">
          {performanceMetrics.lastRun}
        </span>
      </div>
    </div>
  );
}
