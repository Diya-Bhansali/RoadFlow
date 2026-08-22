import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { approachGeometry, cycleLength, signalOffset } from "../data/mockData";

/* ── Collapsible Section ──────────────────────────────────────────────────── */
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
      <button className="panel-section__header" onClick={() => setOpen(!open)}>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span className="panel-section__title">{title}</span>
      </button>
      {open && <div className="panel-section__body">{children}</div>}
    </div>
  );
}

/* ── Slider + numeric input pair ──────────────────────────────────────────── */
function SliderInput({
  label,
  value,
  min,
  max,
  step,
  unit,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit: string;
  onChange: (v: number) => void;
}) {
  return (
    <div className="slider-input">
      <label className="slider-input__label">{label}</label>
      <div className="slider-input__controls">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="slider-input__slider"
        />
        <input
          type="number"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="slider-input__number font-mono"
        />
        <span className="slider-input__unit">{unit}</span>
      </div>
    </div>
  );
}

/* ── RightPanel ───────────────────────────────────────────────────────────── */
export default function RightPanel() {
  /* local state mirrors mock defaults — easy to lift later */
  const [geo, setGeo] = useState(
    approachGeometry.map((a) => ({ ...a }))
  );
  const [cycle, setCycle] = useState(cycleLength);
  const [offset, setOffset] = useState(signalOffset);

  const updateGeo = (idx: number, key: string, val: number) => {
    setGeo((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], [key]: val };
      return next;
    });
  };

  return (
    <aside className="right-panel">
      <h2 className="right-panel__header">DESIGN PARAMETERS</h2>

      {/* ROAD GEOMETRY */}
      <Section title="ROAD GEOMETRY">
        {geo.map((a, i) => (
          <div key={a.direction} className="geo-group">
            <span className="geo-group__dir">{a.direction} Approach</span>
            <SliderInput
              label="Lanes"
              value={a.lanes}
              min={1}
              max={6}
              step={1}
              unit=""
              onChange={(v) => updateGeo(i, "lanes", v)}
            />
            <SliderInput
              label="Lane Width"
              value={a.laneWidth}
              min={2.5}
              max={5.0}
              step={0.1}
              unit="m"
              onChange={(v) => updateGeo(i, "laneWidth", v)}
            />
            <SliderInput
              label="Shoulder Width"
              value={a.shoulderWidth}
              min={0}
              max={2.0}
              step={0.1}
              unit="m"
              onChange={(v) => updateGeo(i, "shoulderWidth", v)}
            />
            <SliderInput
              label="Corner Radius"
              value={a.cornerRadius}
              min={3}
              max={20}
              step={0.5}
              unit="m"
              onChange={(v) => updateGeo(i, "cornerRadius", v)}
            />
          </div>
        ))}
      </Section>

      {/* SIGNAL TIMING */}
      <Section title="SIGNAL TIMING">
        <SliderInput
          label="Cycle Length"
          value={cycle}
          min={30}
          max={240}
          step={1}
          unit="s"
          onChange={setCycle}
        />
        <SliderInput
          label="Offset"
          value={offset}
          min={0}
          max={cycle}
          step={1}
          unit="s"
          onChange={setOffset}
        />
        <button className="edit-phases-btn">
          Edit Signal Phases →
        </button>
      </Section>

      {/* TRAFFIC RULES (collapsed) */}
      <Section title="TRAFFIC RULES" defaultOpen={false}>
        <p className="placeholder-text">
          Speed limits, turn restrictions, and lane-use rules will appear here.
        </p>
      </Section>

      {/* ADVANCED SETTINGS (collapsed) */}
      <Section title="ADVANCED SETTINGS" defaultOpen={false}>
        <p className="placeholder-text">
          Simulation parameters, solver settings, and export options.
        </p>
      </Section>
    </aside>
  );
}
