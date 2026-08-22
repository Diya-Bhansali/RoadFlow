import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Minus,
  MapPin,
} from "lucide-react";
import {
  intersectionInfo,
  trafficDemand,
  type Direction,
} from "../data/mockData";

/* ── Collapsible Section wrapper ──────────────────────────────────────────── */
function Section({
  title,
  defaultOpen = true,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="panel-section">
      <button
        className="panel-section__header"
        onClick={() => setOpen(!open)}
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span className="panel-section__title">{title}</span>
      </button>
      {open && <div className="panel-section__body">{children}</div>}
    </div>
  );
}

/* ── Key / Value row ──────────────────────────────────────────────────────── */
function KV({ label, value }: { label: string; value: string }) {
  return (
    <div className="kv-row">
      <span className="kv-row__label">{label}</span>
      <span className="kv-row__value">{value}</span>
    </div>
  );
}

/* ── Mini bar chart for traffic volumes ───────────────────────────────────── */
function MiniBar({ dir }: { dir: Direction }) {
  const vol = trafficDemand[dir];
  const max = Math.max(vol.through, vol.left, vol.right, 1);
  const total = vol.through + vol.left + vol.right;

  const bars = [
    { label: "T", value: vol.through, color: "var(--accent)" },
    { label: "L", value: vol.left, color: "#f59e0b" },
    { label: "R", value: vol.right, color: "#8b5cf6" },
  ];

  return (
    <div className="mini-bar">
      <span className="mini-bar__dir">{dir[0]}</span>
      <div className="mini-bar__bars">
        {bars.map((b) => (
          <div key={b.label} className="mini-bar__track">
            <div
              className="mini-bar__fill"
              style={{
                width: `${(b.value / max) * 100}%`,
                backgroundColor: b.color,
              }}
            />
            <span className="mini-bar__val font-mono">{b.value}</span>
          </div>
        ))}
      </div>
      <span className="mini-bar__total font-mono">Σ {total}</span>
    </div>
  );
}

/* ── Toggle switch ────────────────────────────────────────────────────────── */
function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="toggle-row">
      <span className="toggle-row__label">{label}</span>
      <div
        className={`toggle-switch ${checked ? "toggle-switch--on" : ""}`}
        onClick={() => onChange(!checked)}
      >
        <div className="toggle-switch__thumb" />
      </div>
    </label>
  );
}

/* ── Main LeftPanel ───────────────────────────────────────────────────────── */
export default function LeftPanel() {
  const [showGrid, setShowGrid] = useState(true);
  const [gridSize, setGridSize] = useState(5);
  const [distUnit, setDistUnit] = useState("Meters");
  const [angleUnit, setAngleUnit] = useState("Degrees");

  return (
    <aside className="left-panel">
      {/* LOCATION */}
      <Section title="LOCATION">
        <div className="location-map">
          <div className="location-map__placeholder">
            <MapPin size={20} className="location-map__pin" />
            <span className="location-map__road location-map__road--1">Karve Rd</span>
            <span className="location-map__road location-map__road--2">Paud Rd</span>
            <span className="location-map__road location-map__road--3">MIT Rd</span>
          </div>
          <div className="location-map__zoom">
            <button className="location-map__zoom-btn"><Plus size={12} /></button>
            <button className="location-map__zoom-btn"><Minus size={12} /></button>
          </div>
        </div>
        <p className="location-coords font-mono">
          18.5074° N, 73.8077° E
        </p>
      </Section>

      {/* INTERSECTION INFO */}
      <Section title="INTERSECTION INFO">
        <KV label="Name" value={intersectionInfo.name} />
        <KV label="ID" value={intersectionInfo.id} />
        <KV label="City" value={intersectionInfo.city} />
        <KV label="Control Type" value={intersectionInfo.controlType} />
        <KV label="Coord. System" value={intersectionInfo.coordinateSystem} />
        <KV label="Reference Point" value={intersectionInfo.referencePoint} />
      </Section>

      {/* UNITS & DISPLAY */}
      <Section title="UNITS & DISPLAY">
        <div className="select-row">
          <label className="select-row__label">Distance Unit</label>
          <select
            className="select-row__select"
            value={distUnit}
            onChange={(e) => setDistUnit(e.target.value)}
          >
            <option>Meters</option>
            <option>Feet</option>
          </select>
        </div>
        <div className="select-row">
          <label className="select-row__label">Angle Unit</label>
          <select
            className="select-row__select"
            value={angleUnit}
            onChange={(e) => setAngleUnit(e.target.value)}
          >
            <option>Degrees</option>
            <option>Radians</option>
          </select>
        </div>
        <Toggle label="Show Grid" checked={showGrid} onChange={setShowGrid} />
        {showGrid && (
          <div className="slider-row">
            <label className="slider-row__label">Grid Size</label>
            <input
              type="range"
              min={1}
              max={20}
              value={gridSize}
              onChange={(e) => setGridSize(Number(e.target.value))}
              className="slider-row__slider"
            />
            <span className="slider-row__value font-mono">{gridSize}m</span>
          </div>
        )}
      </Section>

      {/* TRAFFIC DEMAND */}
      <Section title="TRAFFIC DEMAND">
        <div className="demand-legend">
          <span className="demand-legend__item"><span className="demand-legend__dot" style={{ background: "var(--accent)" }} />Through</span>
          <span className="demand-legend__item"><span className="demand-legend__dot" style={{ background: "#f59e0b" }} />Left</span>
          <span className="demand-legend__item"><span className="demand-legend__dot" style={{ background: "#8b5cf6" }} />Right</span>
        </div>
        {(["North", "South", "East", "West"] as Direction[]).map((d) => (
          <MiniBar key={d} dir={d} />
        ))}
      </Section>
    </aside>
  );
}
