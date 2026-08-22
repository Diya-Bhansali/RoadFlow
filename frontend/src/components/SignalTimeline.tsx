import { signalPhases, cycleLength } from "../data/mockData";

const phaseColors = {
  green:  "#22c55e",
  yellow: "#eab308",
  allRed: "#ef4444",
};

export default function SignalTimeline() {
  const playheadPos = 45; // mock playhead at 45s
  const totalW = cycleLength;

  return (
    <div className="bottom-card">
      <h3 className="bottom-card__title">SIGNAL PHASE TIMELINE</h3>

      <div className="timeline">
        {/* ── Time axis ────────────────────────────────────────── */}
        <div className="timeline__axis">
          {Array.from({ length: 13 }).map((_, i) => (
            <span key={i} className="timeline__tick font-mono">
              {i * 10}
            </span>
          ))}
        </div>

        {/* ── Phase rows ───────────────────────────────────────── */}
        <div className="timeline__rows">
          {signalPhases.map((phase) => {
            const greenStart  = (phase.offset / totalW) * 100;
            const greenW      = (phase.green / totalW) * 100;
            const yellowStart = greenStart + greenW;
            const yellowW     = (phase.yellow / totalW) * 100;
            const redStart    = yellowStart + yellowW;
            const redW        = (phase.allRed / totalW) * 100;

            return (
              <div key={phase.id} className="timeline__row">
                <span className="timeline__row-label">{phase.label}</span>
                <div className="timeline__bar-track">
                  {phase.green > 0 && (
                    <div
                      className="timeline__bar"
                      style={{
                        left: `${greenStart}%`,
                        width: `${greenW}%`,
                        backgroundColor: phaseColors.green,
                      }}
                    >
                      <span className="timeline__bar-dur font-mono">{phase.green}s</span>
                    </div>
                  )}
                  {phase.yellow > 0 && (
                    <div
                      className="timeline__bar"
                      style={{
                        left: `${yellowStart}%`,
                        width: `${yellowW}%`,
                        backgroundColor: phaseColors.yellow,
                      }}
                    >
                      <span className="timeline__bar-dur font-mono">{phase.yellow}s</span>
                    </div>
                  )}
                  {phase.allRed > 0 && (
                    <div
                      className="timeline__bar"
                      style={{
                        left: `${redStart}%`,
                        width: `${redW}%`,
                        backgroundColor: phaseColors.allRed,
                      }}
                    >
                      <span className="timeline__bar-dur font-mono">{phase.allRed}s</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* ── Playhead ───────────────────────────────────────── */}
          <div
            className="timeline__playhead"
            style={{ left: `calc(140px + ${(playheadPos / totalW) * 100}% * (100% - 140px) / 100%)` }}
          />
        </div>

        {/* ── Legend ────────────────────────────────────────────── */}
        <div className="timeline__legend">
          <span className="timeline__legend-item">
            <span className="timeline__legend-dot" style={{ background: phaseColors.green }} />Green
          </span>
          <span className="timeline__legend-item">
            <span className="timeline__legend-dot" style={{ background: phaseColors.yellow }} />Yellow
          </span>
          <span className="timeline__legend-item">
            <span className="timeline__legend-dot" style={{ background: phaseColors.allRed }} />All Red
          </span>
        </div>
      </div>
    </div>
  );
}
