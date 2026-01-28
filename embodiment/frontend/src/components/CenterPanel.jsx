import React, { useRef, useEffect, useState } from 'react';
import useAppStore from '../store';
import { ExpressionEngine } from '../logic/ExpressionEngine';
import FaceRenderer from './FaceRenderer'; // We reuse the logic but style it here or inside

// Split this file if it gets too large, but for now combining as per layout structure
const CenterPanel = () => {
    const emotion = useAppStore((state) => state.emotion);
    const [activeMode, setActiveMode] = useState('Safe');

    // Expression Engine
    const engineRef = useRef(new ExpressionEngine());
    const [expression, setExpression] = useState(engineRef.current.current);
    const [isManual, setIsManual] = useState(false);

    // Animation Loop
    useEffect(() => {
        let frameId;
        let lastTime = performance.now();

        const loop = (now) => {
            const dt = (now - lastTime) / 1000;
            lastTime = now;
            const curr = engineRef.current.update(dt, isManual);
            setExpression({ ...curr }); // Trigger render
            frameId = requestAnimationFrame(loop);
        };
        frameId = requestAnimationFrame(loop);
        return () => cancelAnimationFrame(frameId);
    }, [isManual]);

    // Sync Emotion -> Expression
    useEffect(() => {
        if (!isManual) {
            engineRef.current.updateTargetFromEmotion(emotion);
        }
    }, [emotion, isManual]);

    const handleCommand = async (mode) => {
        setActiveMode(mode);
        try {
            await fetch(`http://localhost:8000/api/command?command=${mode}`, { method: 'POST' });
        } catch (e) { console.error(e); }
    };

    return (
        <div className="flex flex-col gap-5 h-full text-[#1D1D1F]">

            {/* Top: Command Center */}
            <div className="bg-white rounded-[22px] shadow-[0_4px_20px_rgba(0,0,0,0.05)] p-5 flex-none">
                <div className="text-[11px] font-bold text-[#86868B] uppercase tracking-wider mb-3.5">
                    Command Center
                </div>
                <div className="flex bg-[#F2F2F7] p-1 rounded-[14px]">
                    {['Safe', 'Explore', 'Combat'].map(mode => (
                        <button
                            key={mode}
                            onClick={() => handleCommand(mode)}
                            className={`flex-1 py-2.5 text-[13px] font-medium rounded-[10px] transition-all
                ${activeMode === mode
                                    ? 'bg-white text-[#007AFF] shadow-sm font-bold'
                                    : 'text-[#86868B] hover:text-[#1D1D1F]'}`}
                        >
                            {mode}
                        </button>
                    ))}
                </div>
            </div>

            {/* Bottom: Expression Card */}
            <div className="flex-1 bg-gradient-to-b from-white to-[#F9FAFF] rounded-[22px] shadow-[0_4px_20px_rgba(0,0,0,0.05)] p-5 flex flex-col items-center justify-center text-center">

                {/* Face Container: Small Circle */}
                <div className="w-[140px] h-[140px] bg-white rounded-full shadow-[0_10px_40px_rgba(0,122,255,0.1)] flex items-center justify-center mb-6 overflow-hidden relative">
                    {/* Reuse FaceRenderer but constrain it to this container */}
                    <FaceRenderer expression={expression} size={140} />
                </div>

                <p className="text-[13px] text-[#86868B] max-w-[80%] leading-relaxed">
                    "마마, 채팅창이 아주 넓고 시원해졌사옵니다!"
                </p>

                {/* Debug / Info */}
                <div className="mt-8 flex gap-4 text-[10px] text-gray-400 font-mono">
                    <span>FCS: {emotion.focus.toFixed(2)}</span>
                    <span>CNF: {emotion.confidence.toFixed(2)}</span>
                </div>

            </div>

        </div>
    );
};

export default CenterPanel;
