'use client';

import { useState, useEffect } from 'react';
import { MissionState } from '../../types/dashboard';
import { useDashboard } from '../../context/DashboardContext';

interface Props {
  data: MissionState;
}

const statusIcon = (status: MissionState['status']) => {
  const icons = { Nominal: '🟢', Degraded: '🟡', Critical: '🔴' };
  return icons[status];
};

export const DashboardHeader: React.FC<Props> = ({ data }) => {
  const { isConnected } = useDashboard();
  const [time, setTime] = useState(new Date().toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Kolkata',
  }));

  useEffect(() => {
    const iv = setInterval(
      () =>
        setTime(
          new Date().toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
          })
        ),
      1000 * 30
    );
    return () => clearInterval(iv);
  }, []);

  return (
    <header className="h-[100px] lg:h-[80px] bg-black/40 backdrop-blur-md border-b border-teal-500/30 flex items-center px-6 fixed w-full z-50 shadow-[0_4px_30px_rgba(0,0,0,0.5)]">
      <div className="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-teal-500/50 to-transparent animate-pulse-slow" />

      {/* Critical: 3-sec scan path */}
      <div className="flex items-center space-x-6 w-full">
        {/* MISSION STATUS - PRIMARY (32px) */}
        <div className="flex items-center space-x-4 min-w-0 flex-shrink-0">
          <div className="w-16 h-16 bg-gradient-to-br from-teal-500/20 to-cyan-500/20 rounded-2xl glow-teal animate-pulse-slow shadow-2xl border border-teal-500/30 backdrop-blur-sm flex items-center justify-center">
            <span className="text-2xl animate-pulse">🛰️</span>
          </div>
          <div className="min-w-0">
            <h1 className="text-3xl lg:text-2xl font-black font-mono text-transparent bg-clip-text bg-gradient-to-r from-teal-200 to-cyan-200 tracking-widest uppercase truncate glitch-text" data-text={data.name}>
              {data.name}
            </h1>
            <div className="flex items-center space-x-4 mt-1">
              <span className="px-4 py-1 bg-teal-950/50 text-lg rounded-none text-teal-400 font-mono font-bold border-l-2 border-r-2 border-teal-500/50 tracking-widest uppercase">
                {data.phase}
              </span>
              <span className="text-2xl filter drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">{statusIcon(data.status)}</span>
            </div>
          </div>
        </div>

        {/* CONNECTION STATUS - SECONDARY */}
        <div className="flex items-center space-x-6 ml-auto">
          <span className={`px-6 py-2 rounded-none clip-corner text-sm font-mono font-bold border-t border-b ${isConnected
            ? 'bg-green-900/20 text-green-400 border-green-500/50 shadow-[0_0_10px_rgba(34,197,94,0.2)]'
            : 'bg-red-900/20 text-red-500 border-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.2)]'
            }`}>
            {isConnected ? 'SYSTEM_ONLINE' : 'SYSTEM_OFFLINE'}
          </span>
          <div className="flex flex-col items-end font-mono">
            <span className="text-xs text-teal-500/70 tracking-widest">T_MINUS_NOW</span>
            <span className="text-xl text-teal-100 font-bold tracking-widest tabular-nums">{time}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
