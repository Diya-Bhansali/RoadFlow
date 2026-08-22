import { useState } from "react";
import {
  LayoutDashboard,
  Map,
  PencilRuler,
  BarChart3,
  Cone,
  PlayCircle,
  LineChart,
  FileText,
  Settings,
} from "lucide-react";

const iconMap: Record<string, React.ReactNode> = {
  "layout-dashboard": <LayoutDashboard size={20} />,
  map:                <Map size={20} />,
  "pencil-ruler":     <PencilRuler size={20} />,
  "bar-chart-3":      <BarChart3 size={20} />,
  "traffic-cone":     <Cone size={20} />,
  "play-circle":      <PlayCircle size={20} />,
  "line-chart":       <LineChart size={20} />,
  "file-text":        <FileText size={20} />,
  settings:           <Settings size={20} />,
};

import { sideNavItems } from "../data/mockData";

export default function LeftIconRail() {
  const [active, setActive] = useState("Map");

  return (
    <aside className="icon-rail">
      <nav className="icon-rail__nav">
        {sideNavItems.map((item) => (
          <button
            key={item.label}
            className={`icon-rail__btn ${active === item.label ? "icon-rail__btn--active" : ""}`}
            onClick={() => setActive(item.label)}
            title={item.label}
          >
            {iconMap[item.icon]}
            <span className="icon-rail__label">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* User avatar pinned at bottom */}
      <div className="icon-rail__avatar" title="Diya Bhansali">
        <span>DB</span>
      </div>
    </aside>
  );
}
