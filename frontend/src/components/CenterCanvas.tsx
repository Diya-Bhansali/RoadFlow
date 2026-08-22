import { useState } from "react";
import {
  MousePointer2,
  Move,
  Minus,
  Spline,
  CircleDot,
  Ruler,
  ChevronDown,
  Lock,
} from "lucide-react";
import { canvasTools } from "../data/mockData";

const toolIcons: Record<string, React.ReactNode> = {
  Select:  <MousePointer2 size={16} />,
  Move:    <Move size={16} />,
  Lane:    <Minus size={16} />,
  Curve:   <Spline size={16} />,
  Signal:  <CircleDot size={16} />,
  Measure: <Ruler size={16} />,
};

/* ── SVG Intersection Diagram ─────────────────────────────────────────────── */
function IntersectionSVG() {
  const W = 800;
  const H = 700;
  const cx = W / 2;
  const cy = H / 2;
  const roadW = 42; // total road width (3 lanes × 14)
  const laneW = 14;
  const hw = roadW / 2; // half road width

  /* tick positions (meters) */
  const ticks = [-80, -60, -40, -20, 0, 20, 40, 60, 80];

  /* lane labels */
  const lanes: { id: string; x: number; y: number; rot?: number }[] = [
    // North approach (coming from top, left side of road = lanes going south)
    { id: "N1", x: cx - hw + laneW * 0.5, y: cy - hw - 30 },
    { id: "N2", x: cx - hw + laneW * 1.5, y: cy - hw - 30 },
    { id: "N3", x: cx - hw + laneW * 2.5, y: cy - hw - 30 },
    // South approach
    { id: "S1", x: cx + hw - laneW * 2.5, y: cy + hw + 40 },
    { id: "S2", x: cx + hw - laneW * 1.5, y: cy + hw + 40 },
    { id: "S3", x: cx + hw - laneW * 0.5, y: cy + hw + 40 },
    // East approach
    { id: "E1", x: cx + hw + 30, y: cy - hw + laneW * 0.5, rot: 90 },
    { id: "E2", x: cx + hw + 30, y: cy - hw + laneW * 1.5, rot: 90 },
    { id: "E3", x: cx + hw + 30, y: cy - hw + laneW * 2.5, rot: 90 },
    // West approach
    { id: "W1", x: cx - hw - 30, y: cy + hw - laneW * 2.5, rot: 90 },
    { id: "W2", x: cx - hw - 30, y: cy + hw - laneW * 1.5, rot: 90 },
    { id: "W3", x: cx - hw - 30, y: cy + hw - laneW * 0.5, rot: 90 },
  ];

  /* turning movement paths */
  const turnPaths = [
    // N→S through (teal)
    { d: `M ${cx - hw + laneW} 40 L ${cx - hw + laneW} ${H - 40}`, color: "#14b8a6", opacity: 0.5 },
    // S→N through
    { d: `M ${cx + hw - laneW} ${H - 40} L ${cx + hw - laneW} 40`, color: "#14b8a6", opacity: 0.5 },
    // E→W through
    { d: `M ${W - 40} ${cy - hw + laneW} L 40 ${cy - hw + laneW}`, color: "#3b82f6", opacity: 0.5 },
    // W→E through
    { d: `M 40 ${cy + hw - laneW} L ${W - 40} ${cy + hw - laneW}`, color: "#3b82f6", opacity: 0.5 },
    // N→E left turn
    { d: `M ${cx - hw + laneW * 2.5} 80 L ${cx - hw + laneW * 2.5} ${cy - 10} Q ${cx + 10} ${cy - hw + laneW * 2.5} ${W - 80} ${cy - hw + laneW * 2.5}`, color: "#f59e0b", opacity: 0.4 },
    // S→W left turn
    { d: `M ${cx + hw - laneW * 2.5} ${H - 80} L ${cx + hw - laneW * 2.5} ${cy + 10} Q ${cx - 10} ${cy + hw - laneW * 2.5} 80 ${cy + hw - laneW * 2.5}`, color: "#f59e0b", opacity: 0.4 },
    // N→W right turn
    { d: `M ${cx - hw + laneW * 0.5} 80 Q ${cx - hw + laneW * 0.5} ${cy - hw - 5} 80 ${cy + hw - laneW * 0.5}`, color: "#8b5cf6", opacity: 0.4 },
    // E→N right turn
    { d: `M ${W - 80} ${cy - hw + laneW * 0.5} Q ${cx + hw + 5} ${cy - hw + laneW * 0.5} ${cx + hw - laneW * 0.5} 80`, color: "#8b5cf6", opacity: 0.4 },
  ];

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="canvas__svg"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1a2030" strokeWidth="0.5" />
        </pattern>
        <marker id="arrowN" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
          <path d="M0,6 L3,0 L6,6" fill="none" stroke="#5a6a7a" strokeWidth="1" />
        </marker>
        <marker id="arrowS" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
          <path d="M0,0 L3,6 L6,0" fill="none" stroke="#5a6a7a" strokeWidth="1" />
        </marker>
      </defs>

      {/* Grid background */}
      <rect width={W} height={H} fill="url(#grid)" />

      {/* ── Road surfaces ─────────────────────────────────────── */}
      {/* North-South road */}
      <rect x={cx - hw} y={0} width={roadW} height={H} fill="#1a1f2b" />
      {/* East-West road */}
      <rect x={0} y={cy - hw} width={W} height={roadW} fill="#1a1f2b" />
      {/* Intersection center (overlap) */}
      <rect x={cx - hw} y={cy - hw} width={roadW} height={roadW} fill="#1e2433" />

      {/* ── Lane markings (dashed center lines) ───────────────── */}
      {[1, 2].map((i) => (
        <g key={`ns-lane-${i}`}>
          <line
            x1={cx - hw + laneW * i} y1={0}
            x2={cx - hw + laneW * i} y2={cy - hw}
            stroke="#3a4555" strokeWidth="1" strokeDasharray="8 6"
          />
          <line
            x1={cx - hw + laneW * i} y1={cy + hw}
            x2={cx - hw + laneW * i} y2={H}
            stroke="#3a4555" strokeWidth="1" strokeDasharray="8 6"
          />
        </g>
      ))}
      {[1, 2].map((i) => (
        <g key={`ew-lane-${i}`}>
          <line
            x1={0} y1={cy - hw + laneW * i}
            x2={cx - hw} y2={cy - hw + laneW * i}
            stroke="#3a4555" strokeWidth="1" strokeDasharray="8 6"
          />
          <line
            x1={cx + hw} y1={cy - hw + laneW * i}
            x2={W} y2={cy - hw + laneW * i}
            stroke="#3a4555" strokeWidth="1" strokeDasharray="8 6"
          />
        </g>
      ))}

      {/* ── Road edges ────────────────────────────────────────── */}
      {/* NS road edges */}
      <line x1={cx - hw} y1={0} x2={cx - hw} y2={cy - hw} stroke="#4a5568" strokeWidth="1.5" />
      <line x1={cx + hw} y1={0} x2={cx + hw} y2={cy - hw} stroke="#4a5568" strokeWidth="1.5" />
      <line x1={cx - hw} y1={cy + hw} x2={cx - hw} y2={H} stroke="#4a5568" strokeWidth="1.5" />
      <line x1={cx + hw} y1={cy + hw} x2={cx + hw} y2={H} stroke="#4a5568" strokeWidth="1.5" />
      {/* EW road edges */}
      <line x1={0} y1={cy - hw} x2={cx - hw} y2={cy - hw} stroke="#4a5568" strokeWidth="1.5" />
      <line x1={0} y1={cy + hw} x2={cx - hw} y2={cy + hw} stroke="#4a5568" strokeWidth="1.5" />
      <line x1={cx + hw} y1={cy - hw} x2={W} y2={cy - hw} stroke="#4a5568" strokeWidth="1.5" />
      <line x1={cx + hw} y1={cy + hw} x2={W} y2={cy + hw} stroke="#4a5568" strokeWidth="1.5" />

      {/* ── Corner curves ─────────────────────────────────────── */}
      {[
        { sx: cx - hw, sy: cy - hw, dx: -1, dy: -1 }, // NW
        { sx: cx + hw, sy: cy - hw, dx: 1,  dy: -1 }, // NE
        { sx: cx + hw, sy: cy + hw, dx: 1,  dy: 1  }, // SE
        { sx: cx - hw, sy: cy + hw, dx: -1, dy: 1  }, // SW
      ].map((c, i) => (
        <path
          key={`corner-${i}`}
          d={`M ${c.sx} ${c.sy + c.dy * 12} Q ${c.sx} ${c.sy} ${c.sx + c.dx * 12} ${c.sy}`}
          fill="none"
          stroke="#4a5568"
          strokeWidth="1.5"
        />
      ))}

      {/* ── Crosswalk hatching ────────────────────────────────── */}
      {/* North crosswalk */}
      {Array.from({ length: 7 }).map((_, i) => (
        <rect key={`xwN${i}`} x={cx - hw + 2 + i * 6} y={cy - hw - 10} width={4} height={8} fill="#2a3344" rx={0} />
      ))}
      {/* South crosswalk */}
      {Array.from({ length: 7 }).map((_, i) => (
        <rect key={`xwS${i}`} x={cx - hw + 2 + i * 6} y={cy + hw + 2} width={4} height={8} fill="#2a3344" rx={0} />
      ))}
      {/* East crosswalk */}
      {Array.from({ length: 7 }).map((_, i) => (
        <rect key={`xwE${i}`} x={cx + hw + 2} y={cy - hw + 2 + i * 6} width={8} height={4} fill="#2a3344" rx={0} />
      ))}
      {/* West crosswalk */}
      {Array.from({ length: 7 }).map((_, i) => (
        <rect key={`xwW${i}`} x={cx - hw - 10} y={cy - hw + 2 + i * 6} width={8} height={4} fill="#2a3344" rx={0} />
      ))}

      {/* ── Turning movement paths ────────────────────────────── */}
      {turnPaths.map((tp, i) => (
        <path
          key={`turn-${i}`}
          d={tp.d}
          fill="none"
          stroke={tp.color}
          strokeWidth="2"
          opacity={tp.opacity}
          strokeLinecap="round"
        />
      ))}

      {/* ── Directional arrows in lanes ───────────────────────── */}
      {/* North approach — downward arrows */}
      {[0.5, 1.5, 2.5].map((ln, i) => {
        const ax = cx - hw + laneW * ln;
        const ay = cy - hw - 55;
        return (
          <g key={`arrN${i}`}>
            <line x1={ax} y1={ay} x2={ax} y2={ay + 16} stroke="#5a6a7a" strokeWidth="1.5" />
            <polygon points={`${ax - 4},${ay + 12} ${ax},${ay + 20} ${ax + 4},${ay + 12}`} fill="#5a6a7a" />
          </g>
        );
      })}
      {/* South approach — upward arrows */}
      {[0.5, 1.5, 2.5].map((ln, i) => {
        const ax = cx + hw - laneW * (ln + 0);
        const ay = cy + hw + 55;
        return (
          <g key={`arrS${i}`}>
            <line x1={ax} y1={ay} x2={ax} y2={ay - 16} stroke="#5a6a7a" strokeWidth="1.5" />
            <polygon points={`${ax - 4},${ay - 12} ${ax},${ay - 20} ${ax + 4},${ay - 12}`} fill="#5a6a7a" />
          </g>
        );
      })}
      {/* East approach — left arrows */}
      {[0.5, 1.5, 2.5].map((ln, i) => {
        const ax = cx + hw + 55;
        const ay = cy - hw + laneW * ln;
        return (
          <g key={`arrE${i}`}>
            <line x1={ax} y1={ay} x2={ax - 16} y2={ay} stroke="#5a6a7a" strokeWidth="1.5" />
            <polygon points={`${ax - 12},${ay - 4} ${ax - 20},${ay} ${ax - 12},${ay + 4}`} fill="#5a6a7a" />
          </g>
        );
      })}
      {/* West approach — right arrows */}
      {[0.5, 1.5, 2.5].map((ln, i) => {
        const ax = cx - hw - 55;
        const ay = cy + hw - laneW * ln;
        return (
          <g key={`arrW${i}`}>
            <line x1={ax} y1={ay} x2={ax + 16} y2={ay} stroke="#5a6a7a" strokeWidth="1.5" />
            <polygon points={`${ax + 12},${ay - 4} ${ax + 20},${ay} ${ax + 12},${ay + 4}`} fill="#5a6a7a" />
          </g>
        );
      })}

      {/* ── Lane labels ───────────────────────────────────────── */}
      {lanes.map((l) => (
        <text
          key={l.id}
          x={l.x}
          y={l.y}
          textAnchor="middle"
          fontSize="9"
          fontFamily="'JetBrains Mono', monospace"
          fill="#6b7a8a"
          transform={l.rot ? `rotate(${l.rot} ${l.x} ${l.y})` : undefined}
        >
          {l.id}
        </text>
      ))}

      {/* ── Axis tick labels ──────────────────────────────────── */}
      {ticks.map((t) => {
        const px = cx + t * 4;
        const py = cy + t * 4;
        return (
          <g key={`tick-${t}`}>
            {/* x-axis (bottom) */}
            <text x={px} y={H - 8} textAnchor="middle" fontSize="8" fontFamily="'JetBrains Mono', monospace" fill="#4a5568">
              {t}
            </text>
            <line x1={px} y1={H - 18} x2={px} y2={H - 14} stroke="#4a5568" strokeWidth="0.5" />
            {/* y-axis (left) */}
            <text x={12} y={py + 3} textAnchor="start" fontSize="8" fontFamily="'JetBrains Mono', monospace" fill="#4a5568">
              {-t}
            </text>
            <line x1={28} y1={py} x2={32} y2={py} stroke="#4a5568" strokeWidth="0.5" />
          </g>
        );
      })}
    </svg>
  );
}

/* ── CenterCanvas ─────────────────────────────────────────────────────────── */
export default function CenterCanvas() {
  const [activeTool, setActiveTool] = useState<string>("Select");
  const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width * 200 - 100).toFixed(1);
    const y = (-(((e.clientY - rect.top) / rect.height) * 200 - 100)).toFixed(1);
    setCursorPos({ x: Number(x), y: Number(y) });
  };

  return (
    <div className="canvas" onMouseMove={handleMouseMove}>
      {/* ── Toolbar strip ─────────────────────────────────────── */}
      <div className="canvas__toolbar">
        {canvasTools.map((tool) => (
          <button
            key={tool}
            className={`canvas__tool ${activeTool === tool ? "canvas__tool--active" : ""}`}
            onClick={() => setActiveTool(tool)}
          >
            {toolIcons[tool]}
            <span>{tool}</span>
          </button>
        ))}
        <button className="canvas__tool canvas__tool--dropdown">
          <span>Add Object</span>
          <ChevronDown size={14} />
        </button>
      </div>

      {/* ── SVG viewport ──────────────────────────────────────── */}
      <div className="canvas__viewport">
        <IntersectionSVG />

        {/* Coordinate readout (bottom-left) */}
        <div className="canvas__readout font-mono">
          <span>X: {cursorPos.x}m</span>
          <span>Y: {cursorPos.y}m</span>
          <span className="canvas__readout-divider">|</span>
          <span>Scale 1:200</span>
        </div>

        {/* Lock icon (bottom-right) */}
        <button className="canvas__lock" title="Lock view">
          <Lock size={14} />
        </button>
      </div>
    </div>
  );
}
