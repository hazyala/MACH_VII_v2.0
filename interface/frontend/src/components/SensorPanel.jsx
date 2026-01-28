import React from 'react';
import { Eye, Ruler } from 'lucide-react';

const SensorPanel = ({ perception }) => {
    // Expect perception.depth_grid to be array of 9 floats (cm)
    // If undefined, default to zeros
    const grid = perception.depth_grid || new Array(9).fill(0);

    // Helper to colorize depth cells
    const getCellColor = (val) => {
        if (val === 0) return 'bg-gray-900'; // No Data / Too Far
        if (val < 20) return 'bg-red-600';   // Too Close
        if (val < 50) return 'bg-yellow-600'; // Warning
        return 'bg-green-800'; // Safe
    };

    return (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 shadow-lg flex flex-col h-full">
            <h3 className="text-gray-400 text-sm font-bold mb-3 uppercase flex items-center gap-2">
                <Eye className="w-4 h-4 text-cyan-400" /> Depth Sensor Grid
            </h3>

            <div className="flex-1 flex flex-col items-center justify-center relative">
                {/* 3x3 Heatmap */}
                <div className="grid grid-cols-3 gap-1 w-full max-w-[200px] aspect-square">
                    {grid.map((val, idx) => (
                        <div
                            key={idx}
                            className={`rounded flex items-center justify-center transition-colors duration-100 ${getCellColor(val)}`}
                        >
                            <span className="text-[10px] font-mono text-white/50">{val.toFixed(0)}</span>
                        </div>
                    ))}
                </div>

                {/* Center Distance Overlay */}
                <div className="mt-4 bg-black/60 px-4 py-2 rounded-full border border-gray-600 flex items-center gap-2 backdrop-blur-sm">
                    <Ruler className="w-4 h-4 text-gray-400" />
                    <span className="text-xl font-mono font-bold text-white">
                        {perception.obstacle_distance_cm.toFixed(1)} <span className="text-xs text-gray-500 font-normal">cm</span>
                    </span>
                </div>
            </div>
        </div>
    );
};

export default SensorPanel;
