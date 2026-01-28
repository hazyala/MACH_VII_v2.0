import React, { useRef } from 'react';
import useAppStore from '../store';

const SensorPanel = () => {
    // Use selectors for performance
    const perception = useAppStore((state) => state.perception);

    // Refs for direct DOM manipulation if needed for video streams later
    const rgbRef = useRef(null);
    const depthRef = useRef(null);

    return (
        <div className="flex flex-col gap-5 h-full">
            {/* RGB Camera Card */}
            <div className="flex-1 bg-[#F2F2F7] rounded-[22px] relative overflow-hidden shadow-sm">
                <div className="absolute top-3.5 left-3.5 bg-white/85 px-2.5 py-1.5 rounded-[10px] 
                        text-[10px] font-bold text-[#1D1D1F] backdrop-blur-sm z-10">
                    LIVE RGB
                </div>
                {/* Placeholder for Video Feed */}
                <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
                    <img
                        src="https://picsum.photos/id/1/600/400"
                        alt="RGB Feed"
                        className="w-full h-full object-cover opacity-80"
                    />
                    {/* If real stream available: <canvas ref={rgbRef} ... /> */}
                </div>
            </div>

            {/* Depth Camera Card */}
            <div className="flex-1 bg-[#F2F2F7] rounded-[22px] relative overflow-hidden shadow-sm">
                <div className="absolute top-3.5 left-3.5 bg-white/85 px-2.5 py-1.5 rounded-[10px] 
                        text-[10px] font-bold text-[#1D1D1F] backdrop-blur-sm z-10">
                    DEPTH MAP
                </div>
                <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
                    <img
                        src="https://picsum.photos/id/10/600/400?grayscale"
                        alt="Depth Feed"
                        className="w-full h-full object-cover opacity-50"
                    />
                </div>

                {/* Sensor Stats Overlay */}
                <div className="absolute bottom-4 left-4 right-4 flex gap-2">
                    <div className="bg-black/10 backdrop-blur-md px-3 py-1 rounded-lg text-[10px] text-gray-600 font-mono">
                        OBJ: {perception.obstacle_distance_cm}cm
                    </div>
                    <div className="bg-black/10 backdrop-blur-md px-3 py-1 rounded-lg text-[10px] text-gray-600 font-mono">
                        RISK: {perception.risk_level}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default React.memo(SensorPanel);
