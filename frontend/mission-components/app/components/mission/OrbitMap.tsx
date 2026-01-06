import React from 'react';
import { Satellite, AnomalyEvent } from '../../types/dashboard';

interface Props {
  satellites: Satellite[];
  selectedSat?: Satellite | null;
  onSatClick: (sat: Satellite) => void;
  anomalies: AnomalyEvent[];
}

export const OrbitMap: React.FC<Props> = ({ satellites, selectedSat, onSatClick, anomalies }) => {
  const getColorByStatus = (status: string) => {
    switch (status) {
      case 'Nominal':
        return { stroke: '#22c55e', fill: '#22c55e' }; // Green-500
      case 'Degraded':
        return { stroke: '#eab308', fill: '#eab308' }; // Yellow-500
      case 'Critical':
        return { stroke: '#ef4444', fill: '#ef4444' }; // Red-500
      default:
        return { stroke: '#94a3b8', fill: '#94a3b8' }; // Slate-400
    }
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-slate-950 rounded-sm border border-slate-900 overflow-hidden">
      <svg viewBox="0 0 800 600" className="w-full h-full max-h-96" preserveAspectRatio="xMidYMid meet">
        <defs>
          <radialGradient id="earthGrad" cx="50%" cy="50%">
            <stop offset="0%" stopColor="#1e293b" /> {/* Slate-800 */}
            <stop offset="100%" stopColor="#0f172a" /> {/* Slate-900 */}
          </radialGradient>
        </defs>

        {/* Earth Representation */}
        <circle
          cx="400"
          cy="300"
          r="140"
          fill="url(#earthGrad)"
          stroke="#334155" /* Slate-700 */
          strokeWidth="1"
          opacity="0.5"
        />

        {/* Tactical Grid (Subtle) */}
        <g className="opacity-20">
          {/* Crosshairs */}
          <line x1="0" y1="300" x2="800" y2="300" stroke="#94a3b8" strokeWidth="0.5" strokeDasharray="4,4" />
          <line x1="400" y1="0" x2="400" y2="600" stroke="#94a3b8" strokeWidth="0.5" strokeDasharray="4,4" />

          {/* Range Rings */}
          {[100, 200, 300, 400].map((r) => (
            <circle
              key={`range-${r}`}
              cx="400"
              cy="300"
              r={r}
              fill="none"
              stroke="#94a3b8"
              strokeWidth="0.5"
            />
          ))}
        </g>

        {/* Satellites */}
        {satellites.map((sat, idx) => {
          const baseAngle = (idx * (Math.PI * 2)) / satellites.length;
          const timeOffset = Date.now() * 0.00005 + idx; // Slower, more stable movement
          const angle = baseAngle + timeOffset;

          const orbitRadius = 220;
          const x = 400 + Math.cos(angle) * orbitRadius;
          const y = 300 + Math.sin(angle) * orbitRadius;

          const colors = getColorByStatus(sat.status);
          const isSelected = selectedSat?.id === sat.id;
          const radius = isSelected ? 6 : 4;

          return (
            <g key={sat.id}>
              {/* Orbit Path Segment */}
              <circle
                cx="400"
                cy="300"
                r={orbitRadius}
                fill="none"
                stroke="#334155"
                strokeWidth="1"
                opacity="0.1"
                strokeDasharray="2,4"
              />

              {/* Satellite Dot */}
              <g
                onClick={() => onSatClick(sat)}
                className="cursor-pointer hover:opacity-100 transition-opacity"
                style={{ opacity: isSelected ? 1 : 0.8 }}
              >
                <circle
                  cx={x}
                  cy={y}
                  r={radius}
                  fill={colors.fill}
                  stroke={isSelected ? '#f8fafc' : 'none'}
                  strokeWidth={isSelected ? 2 : 0}
                />

                {/* Selection Indicator */}
                {isSelected && (
                  <circle
                    cx={x}
                    cy={y}
                    r={radius + 4}
                    fill="none"
                    stroke={colors.stroke}
                    strokeWidth="1"
                    opacity="0.5"
                  />
                )}
              </g>

              {/* Label */}
              <text
                x={x + 10}
                y={y}
                fontSize="10"
                fill={isSelected ? '#f8fafc' : '#94a3b8'}
                className="font-mono uppercase tracking-wider select-none pointer-events-none"
              >
                {sat.orbitSlot}
              </text>
            </g>
          );
        })}

        {/* Anomalies */}
        {anomalies.slice(0, 3).map((anomaly) => {
          const satIndex = satellites.findIndex((s) => s.orbitSlot === anomaly.satellite.split('-')[1]);
          if (satIndex === -1) return null;

          const baseAngle = (satIndex * (Math.PI * 2)) / satellites.length;
          const timeOffset = Date.now() * 0.00005 + satIndex;
          const angle = baseAngle + timeOffset;
          const x = 400 + Math.cos(angle) * 220;
          const y = 300 + Math.sin(angle) * 220;

          return (
            <g key={anomaly.id}>
              <circle
                cx={x}
                cy={y}
                r="12"
                fill="none"
                stroke="#ef4444"
                strokeWidth="1"
                strokeDasharray="2,2"
                opacity="0.6"
              >
                <animate attributeName="r" values="10;14;10" dur="2s" repeatCount="indefinite" />
              </circle>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
