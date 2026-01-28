import React from 'react';
import { Play, AlertTriangle, Compass, Shield } from 'lucide-react';

const ControlPanel = ({ onCommand, isManual, onToggleManual }) => {
    return (
        // FORCED VISIBILITY: Fixed position to bypass parent overflow issues
        <div className="fixed bottom-6 right-6 z-[9999] w-80 bg-gray-800 rounded-xl border border-gray-700 p-4 shadow-2xl ring-2 ring-cyan-500/50">
            <h3 className="text-gray-400 text-sm font-bold mb-3 uppercase flex items-center justify-between gap-2">
                <span className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" /> Manual Override
                </span>
                <span className="text-[10px] font-mono text-gray-500">
                    STATE: {(!!isManual).toString().toUpperCase()}
                </span>
            </h3>

            {/* Manual Toggle (Added for visibility) */}
            <button
                onClick={onToggleManual}
                className={`w-full py-3 rounded-lg text-sm font-black transition-all mb-4 flex items-center justify-center gap-2 border shadow-lg ${isManual
                    ? 'bg-yellow-500 hover:bg-yellow-400 text-black border-yellow-300 ring-2 ring-yellow-500/50'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300 border-gray-600'
                    }`}
            >
                {/* Removed Icon to prevent potential crash if import fails */}
                {isManual ? '⚠️ MANUAL OVERRIDE: ON' : '⚙️ ENABLE MANUAL CONTROL'}
            </button>

            <div className="grid grid-cols-2 gap-3">
                <button
                    onClick={() => onCommand('task_start')}
                    className="flex items-center justify-center gap-2 bg-cyan-900/40 hover:bg-cyan-800/60 border border-cyan-800/50 text-cyan-200 p-3 rounded-lg transition-all active:scale-95"
                >
                    <Play className="w-4 h-4" /> Start
                </button>

                <button
                    onClick={() => onCommand('task_fail')}
                    className="flex items-center justify-center gap-2 bg-red-900/40 hover:bg-red-800/60 border border-red-800/50 text-red-200 p-3 rounded-lg transition-all active:scale-95"
                >
                    <AlertTriangle className="w-4 h-4" /> Fail
                </button>

                <button
                    onClick={() => onCommand('explore')}
                    className="flex items-center justify-center gap-2 bg-purple-900/40 hover:bg-purple-800/60 border border-purple-800/50 text-purple-200 p-3 rounded-lg transition-all active:scale-95"
                >
                    <Compass className="w-4 h-4" /> Explore
                </button>

                <button
                    onClick={() => onCommand('safe')}
                    className="flex items-center justify-center gap-2 bg-green-900/40 hover:bg-green-800/60 border border-green-800/50 text-green-200 p-3 rounded-lg transition-all active:scale-95"
                >
                    <Shield className="w-4 h-4" /> Safe
                </button>
            </div>
        </div>
    );
};

export default ControlPanel;
