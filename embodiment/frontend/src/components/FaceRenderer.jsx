import React, { useEffect, useRef } from 'react';
import useAppStore from '../store';
import { ExpressionEngine } from '../logic/ExpressionEngine';

const FaceRenderer = ({ size = 140 }) => {
    const emotion = useAppStore((state) => state.emotion);

    // Internal Engine
    const engineRef = useRef(new ExpressionEngine());

    // DOM Refs for Direct Manipulation
    const leftEyeRef = useRef(null);
    const rightEyeRef = useRef(null);
    const mouthRef = useRef(null);
    const faceGroupRef = useRef(null); // For Head Roll

    // Sync Emotion Store -> Engine Target
    useEffect(() => {
        engineRef.current.updateTargetFromEmotion(emotion);
    }, [emotion]);

    // Animation Loop (60fps, No React Render)
    useEffect(() => {
        let frameId;
        let lastTime = performance.now();

        const loop = (now) => {
            const dt = (now - lastTime) / 1000;
            lastTime = now;

            // 1. Update Physics/Interpolation
            const curr = engineRef.current.update(dt, false); // isManual=false

            // 2. Direct DOM Updates
            // Eye Openness (Scale Y)
            const leftOpen = curr.leftEye?.openness ?? 1.0;
            const rightOpen = curr.rightEye?.openness ?? 1.0;
            if (leftEyeRef.current) leftEyeRef.current.setAttribute('ry', 15 * leftOpen);
            if (rightEyeRef.current) rightEyeRef.current.setAttribute('ry', 15 * rightOpen);

            // Head Roll
            const roll = curr.head?.roll ?? 0.0;
            if (faceGroupRef.current) {
                faceGroupRef.current.setAttribute('transform', `rotate(${roll}, 100, 100)`);
            }

            // Mouth Shape
            // Simple Quadratic Bezier: M 70 120 Q 100 [ControlY] 130 120
            // Happiness 0 -> Straight (120), 1 -> Smile (140), -1 -> Frown (100)
            const happiness = curr.happiness ?? 0.0;
            const controlY = 120 + (happiness * 20);
            if (mouthRef.current) {
                mouthRef.current.setAttribute('d', `M 70 120 Q 100 ${controlY} 130 120`);
            }

            frameId = requestAnimationFrame(loop);
        };

        frameId = requestAnimationFrame(loop);
        return () => cancelAnimationFrame(frameId);
    }, []);

    const faceColor = "#1D1D1F";

    return (
        <div className="w-full h-full flex items-center justify-center">
            <svg
                width="100%"
                height="100%"
                viewBox="0 0 200 200"
                style={{ overflow: 'visible' }}
            >
                {/* Global Transform Group */}
                <g ref={faceGroupRef}>

                    {/* Left Eye */}
                    <g transform="translate(70, 80)">
                        <ellipse
                            ref={leftEyeRef}
                            cx="0" cy="0"
                            rx="12" ry="15"
                            fill={faceColor}
                        />
                        <circle cx="3" cy="-4" r="3" fill="white" opacity="0.2" />
                    </g>

                    {/* Right Eye */}
                    <g transform="translate(130, 80)">
                        <ellipse
                            ref={rightEyeRef}
                            cx="0" cy="0"
                            rx="12" ry="15"
                            fill={faceColor}
                        />
                        <circle cx="3" cy="-4" r="3" fill="white" opacity="0.2" />
                    </g>

                    {/* Mouth */}
                    <path
                        ref={mouthRef}
                        d="M 70 120 Q 100 120 130 120"
                        stroke={faceColor}
                        strokeWidth="4"
                        fill="none"
                        strokeLinecap="round"
                    />

                </g>
            </svg>
        </div>
    );
};

export default React.memo(FaceRenderer);
