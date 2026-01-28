import React from 'react';
import ControlPanel from './ControlPanel'; // Imported
import FaceRenderer from './FaceRenderer'; // Imported
import useAppStore from '../store';

const CenterPanel = () => {
    // We can use store here for debug info if needed
    const emotion = useAppStore((state) => state.emotion);

    return (
        <div className="flex flex-col h-full text-[#1D1D1F] box-border pb-5"> {/* Added pb-5 to match others if needed */}

            {/* Top: Control */}
            <ControlPanel />

            {/* Bottom: Expression Card */}
            <div className="flex-1 bg-gradient-to-b from-white to-[#F9FAFF] rounded-[22px] shadow-[0_4px_20px_rgba(0,0,0,0.05)] p-5 flex flex-col items-center justify-center text-center">

                {/* Face Container */}
                <div className="w-[140px] h-[140px] bg-white rounded-full shadow-[0_10px_40px_rgba(0,122,255,0.1)] flex items-center justify-center mb-6 overflow-hidden relative shrink-0">
                    <FaceRenderer size={140} />
                </div>

                <p className="text-[13px] text-[#86868B] max-w-[80%] leading-relaxed">
                    "마마, 채팅창이 아주 넓고 시원해졌사옵니다!"
                </p>

                {/* Debug Info */}
                <div className="mt-8 flex gap-4 text-[10px] text-gray-400 font-mono">
                    <span>FCS: {emotion.focus.toFixed(2)}</span>
                    <span>CNF: {emotion.confidence.toFixed(2)}</span>
                </div>

            </div>

        </div>
    );
};

export default CenterPanel;
