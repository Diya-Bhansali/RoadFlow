import { useState } from "react";
import {
  Play,
  Pause,
  SkipForward,
  ChevronDown,
} from "lucide-react";
import { simVehicles, vehicleClasses } from "../data/mockData";

export default function SimulationPlayback() {
  const [playing, setPlaying] = useState(false);
  const [elapsed] = useState(45);
  const total = 120;

  return (
    <div className="bottom-card">
      <h3 className="bottom-card__title">SIMULATION PLAYBACK</h3>

      {/* ── Mini intersection map ─────────────────────────────── */}
      <div className="playback__map">
        <svg viewBox="-100 -100 200 200" className="playback__svg">
          {/* Roads */}
          <rect x={-15} y={-100} width={30} height={200} fill="#1a1f2b" />
          <rect x={-100} y={-15} width={200} height={30} fill="#1a1f2b" />
          <rect x={-15} y={-15} width={30} height={30} fill="#1e2433" />

          {/* Road edges */}
          <line x1={-15} y1={-100} x2={-15} y2={100} stroke="#3a4555" strokeWidth="0.5" />
          <line x1={15} y1={-100} x2={15} y2={100} stroke="#3a4555" strokeWidth="0.5" />
          <line x1={-100} y1={-15} x2={100} y2={-15} stroke="#3a4555" strokeWidth="0.5" />
          <line x1={-100} y1={15} x2={100} y2={15} stroke="#3a4555" strokeWidth="0.5" />

          {/* Vehicles */}
          {simVehicles.map((v) => (
            <circle
              key={v.id}
              cx={v.x}
              cy={v.y}
              r={3}
              fill={v.color}
              opacity={0.9}
            />
          ))}
        </svg>
      </div>

      {/* ── Playback controls ─────────────────────────────────── */}
      <div className="playback__controls">
        <button
          className="playback__btn"
          onClick={() => setPlaying(!playing)}
          title={playing ? "Pause" : "Play"}
        >
          {playing ? <Pause size={14} /> : <Play size={14} fill="currentColor" />}
        </button>
        <button className="playback__btn" title="Skip">
          <SkipForward size={14} />
        </button>

        <button className="playback__speed">
          1.0x <ChevronDown size={10} />
        </button>

        <input
          type="range"
          min={0}
          max={total}
          value={elapsed}
          readOnly
          className="playback__scrub"
        />

        <span className="playback__time font-mono">
          {elapsed}s / {total}s
        </span>
      </div>

      {/* ── Vehicle legend ─────────────────────────────────────── */}
      <div className="playback__legend">
        {vehicleClasses.map((vc) => (
          <span key={vc.label} className="playback__legend-item">
            <span
              className="playback__legend-dot"
              style={{ background: vc.color }}
            />
            {vc.label}
          </span>
        ))}
      </div>
    </div>
  );
}
