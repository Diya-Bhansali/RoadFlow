import { useState } from "react";
import {
  Undo2,
  Redo2,
  Share2,
  Play,
  MoreVertical,
} from "lucide-react";
import { topTabs, intersectionInfo } from "../data/mockData";

export default function TopBar() {
  const [activeTab, setActiveTab] = useState<string>("Design");

  return (
    <header className="topbar">
      {/* ── Left: Logo + Intersection ──────────────────────────── */}
      <div className="topbar__left">
        <span className="topbar__logo">
          <span className="topbar__logo-road">Road</span>
          <span className="topbar__logo-flow">Flow</span>
        </span>

        <span className="topbar__divider" />

        <span className="topbar__intersection">
          {intersectionInfo.name}
          <span className="topbar__saved-dot" title="Saved" />
        </span>
      </div>

      {/* ── Center: Tabs ───────────────────────────────────────── */}
      <nav className="topbar__tabs">
        {topTabs.map((tab) => (
          <button
            key={tab}
            className={`topbar__tab ${activeTab === tab ? "topbar__tab--active" : ""}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>

      {/* ── Right: Actions ─────────────────────────────────────── */}
      <div className="topbar__actions">
        <button className="topbar__icon-btn" title="Undo">
          <Undo2 size={16} />
        </button>
        <button className="topbar__icon-btn" title="Redo">
          <Redo2 size={16} />
        </button>

        <button className="topbar__btn-outline">
          <Share2 size={14} />
          <span>Share</span>
        </button>

        <button className="topbar__btn-primary">
          <Play size={14} fill="currentColor" />
          <span>Run Simulation</span>
        </button>

        <button className="topbar__icon-btn" title="More">
          <MoreVertical size={16} />
        </button>
      </div>
    </header>
  );
}
