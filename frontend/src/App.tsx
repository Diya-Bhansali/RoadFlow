import TopBar from "./components/TopBar";
import LeftIconRail from "./components/LeftIconRail";
import LeftPanel from "./components/LeftPanel";
import CenterCanvas from "./components/CenterCanvas";
import RightPanel from "./components/RightPanel";
import SignalTimeline from "./components/SignalTimeline";
import SimulationPlayback from "./components/SimulationPlayback";
import PerformanceSnapshot from "./components/PerformanceSnapshot";

export default function App() {
  return (
    <div className="app">
      {/* ── Zone 1: Top Bar ─────────────────────────────────────── */}
      <TopBar />

      {/* ── Main body (below top bar) ──────────────────────────── */}
      <div className="app__body">
        {/* Zone 2: Left Icon Rail */}
        <LeftIconRail />

        {/* Zone 3: Left Panel */}
        <LeftPanel />

        {/* Zone 4: Center Canvas */}
        <div className="app__center">
          <CenterCanvas />

          {/* Zone 6: Bottom Row (3 cards) */}
          <div className="app__bottom-row">
            <SignalTimeline />
            <SimulationPlayback />
            <PerformanceSnapshot />
          </div>
        </div>

        {/* Zone 5: Right Panel */}
        <RightPanel />
      </div>
    </div>
  );
}
