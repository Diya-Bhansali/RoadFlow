// ---------------------------------------------------------------------------
// mockData.ts — Typed mock data matching the FastAPI / Pydantic contract
// ---------------------------------------------------------------------------

// ── Intersection Info ────────────────────────────────────────────────────────

export interface IntersectionInfo {
  name: string;
  id: string;
  city: string;
  controlType: string;
  coordinateSystem: string;
  referencePoint: string;
  lat: number;
  lng: number;
}

export const intersectionInfo: IntersectionInfo = {
  name: "Kothrud 4-Way Intersection",
  id: "INT-KTD-0042",
  city: "Pune, Maharashtra",
  controlType: "Pre-Timed Signal",
  coordinateSystem: "WGS 84",
  referencePoint: "18.5074° N, 73.8077° E",
  lat: 18.5074,
  lng: 73.8077,
};

// ── Approach / Lane Geometry ─────────────────────────────────────────────────

export type Direction = "North" | "South" | "East" | "West";

export interface ApproachGeometry {
  direction: Direction;
  lanes: number;
  laneWidth: number;      // metres
  shoulderWidth: number;  // metres
  cornerRadius: number;   // metres
}

export const approachGeometry: ApproachGeometry[] = [
  { direction: "North", lanes: 3, laneWidth: 3.5, shoulderWidth: 0.5, cornerRadius: 9.0 },
  { direction: "South", lanes: 3, laneWidth: 3.5, shoulderWidth: 0.5, cornerRadius: 9.0 },
  { direction: "East",  lanes: 3, laneWidth: 3.5, shoulderWidth: 0.5, cornerRadius: 9.0 },
  { direction: "West",  lanes: 3, laneWidth: 3.5, shoulderWidth: 0.5, cornerRadius: 9.0 },
];

// ── Signal Timing ────────────────────────────────────────────────────────────

export interface SignalPhase {
  id: number;
  label: string;
  green: number;    // seconds
  yellow: number;   // seconds
  allRed: number;   // seconds
  offset: number;   // start offset within cycle
}

export const cycleLength = 120; // seconds
export const signalOffset = 0;

export const signalPhases: SignalPhase[] = [
  { id: 1, label: "NS Through + Right", green: 35, yellow: 4, allRed: 2, offset: 0  },
  { id: 2, label: "NS Left",            green: 15, yellow: 3, allRed: 2, offset: 41 },
  { id: 3, label: "EW Through + Right", green: 30, yellow: 4, allRed: 2, offset: 61 },
  { id: 4, label: "EW Left",            green: 12, yellow: 3, allRed: 2, offset: 97 },
  { id: 5, label: "All Red",            green: 0,  yellow: 0, allRed: 6, offset: 114 },
];

// ── Traffic Demand ───────────────────────────────────────────────────────────

export interface MovementVolume {
  through: number;  // veh/hr
  left: number;
  right: number;
}

export const trafficDemand: Record<Direction, MovementVolume> = {
  North: { through: 520, left: 180, right: 140 },
  South: { through: 480, left: 160, right: 120 },
  East:  { through: 610, left: 200, right: 170 },
  West:  { through: 440, left: 150, right: 130 },
};

// ── Vehicle Types (matching Pydantic Vehicle model) ──────────────────────────

export interface VehicleClass {
  label: string;
  color: string;
  length: number;
  maxAccel: number;
  maxDecel: number;
  desiredSpeed: number;
}

export const vehicleClasses: VehicleClass[] = [
  { label: "Car",             color: "#3b82f6", length: 4.5, maxAccel: 2.5, maxDecel: 4.0, desiredSpeed: 13.9 },
  { label: "Two Wheeler",     color: "#f59e0b", length: 2.0, maxAccel: 3.0, maxDecel: 5.0, desiredSpeed: 11.1 },
  { label: "Auto Rickshaw",   color: "#10b981", length: 3.2, maxAccel: 1.8, maxDecel: 3.5, desiredSpeed: 8.3  },
  { label: "Bus",             color: "#ef4444", length: 12.0, maxAccel: 1.2, maxDecel: 3.0, desiredSpeed: 11.1 },
  { label: "Truck",           color: "#8b5cf6", length: 10.0, maxAccel: 1.0, maxDecel: 2.5, desiredSpeed: 9.7  },
];

// ── Simulated Vehicle Positions (for playback mini-map) ──────────────────────

export interface SimVehicle {
  id: number;
  x: number;
  y: number;
  type: string;
  color: string;
}

export const simVehicles: SimVehicle[] = [
  { id: 1,  x: -15, y: 60,  type: "Car",           color: "#3b82f6" },
  { id: 2,  x: -15, y: 40,  type: "Car",           color: "#3b82f6" },
  { id: 3,  x: -12, y: 25,  type: "Two Wheeler",   color: "#f59e0b" },
  { id: 4,  x: 15,  y: -35, type: "Car",           color: "#3b82f6" },
  { id: 5,  x: 15,  y: -55, type: "Auto Rickshaw", color: "#10b981" },
  { id: 6,  x: 55,  y: 12,  type: "Bus",           color: "#ef4444" },
  { id: 7,  x: 35,  y: 15,  type: "Two Wheeler",   color: "#f59e0b" },
  { id: 8,  x: -40, y: -12, type: "Truck",         color: "#8b5cf6" },
  { id: 9,  x: -60, y: -15, type: "Car",           color: "#3b82f6" },
  { id: 10, x: 12,  y: -70, type: "Two Wheeler",   color: "#f59e0b" },
  { id: 11, x: -8,  y: 80,  type: "Auto Rickshaw", color: "#10b981" },
  { id: 12, x: 70,  y: -8,  type: "Car",           color: "#3b82f6" },
];

// ── Performance Metrics ──────────────────────────────────────────────────────

export interface PerformanceMetrics {
  avgDelay: string;
  avgQueueLength: string;
  queue95th: string;
  throughput: string;
  safetyIndex: string;
  lastRun: string;
}

export const performanceMetrics: PerformanceMetrics = {
  avgDelay: "32.4 s/veh",
  avgQueueLength: "12.7 veh",
  queue95th: "24.1 veh",
  throughput: "2,840 veh/hr",
  safetyIndex: "0.87",
  lastRun: "2026-08-22 10:48:12",
};

// ── Units & Display defaults ─────────────────────────────────────────────────

export const distanceUnits = ["Meters", "Feet"] as const;
export const angleUnits    = ["Degrees", "Radians"] as const;

// ── Canvas Tool definitions ──────────────────────────────────────────────────

export const canvasTools = [
  "Select", "Move", "Lane", "Curve", "Signal", "Measure",
] as const;

// ── Navigation tabs ──────────────────────────────────────────────────────────

export const topTabs = ["Design", "Simulation", "Optimization", "Results"] as const;

export const sideNavItems = [
  { label: "Dashboard",  icon: "layout-dashboard" },
  { label: "Map",        icon: "map" },
  { label: "Design",     icon: "pencil-ruler" },
  { label: "Demand",     icon: "bar-chart-3" },
  { label: "Signals",    icon: "traffic-cone" },
  { label: "Simulation", icon: "play-circle" },
  { label: "Results",    icon: "line-chart" },
  { label: "Reports",    icon: "file-text" },
  { label: "Settings",   icon: "settings" },
] as const;
