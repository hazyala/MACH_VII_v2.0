import React, { useState, useEffect } from 'react';
import Eye from './Eye';
import Mouth from './Mouth';
import { motion } from 'framer-motion';

const FaceRenderer = ({
    eyeOpenness = 1.0,
    mouthCurve = 0,
    mouthOpenness = 0,
    mouthX = 0,
    mouthY = 0,
    eyeSqueeze = 0,
    eyeSmile = 0,
    gazeX = 0,
    gazeY = 0,
    color = "#FFFFFF",
    glowIntensity = 0.5,
    isAlive = true
}) => {
    const CANVAS_SIZE = 400;

    // -- Liveness State --
    const [blinkState, setBlinkState] = useState(1.0);
    const [jitter, setJitter] = useState({ x: 0, y: 0 });

    // 1. Blinking Logic
    useEffect(() => {
        if (!isAlive) return;

        let timeout;
        const triggerBlink = () => {
            setBlinkState(0);
            setTimeout(() => setBlinkState(1), 150);

            const nextInterval = Math.random() * 4000 + 2000;
            timeout = setTimeout(triggerBlink, nextInterval);
        };

        timeout = setTimeout(triggerBlink, 3000);
        return () => clearTimeout(timeout);
    }, [isAlive]);

    // 2. Micro-saccades (Jitter) Logic
    useEffect(() => {
        if (!isAlive) return;

        const interval = setInterval(() => {
            setJitter({
                x: (Math.random() - 0.5) * 2,
                y: (Math.random() - 0.5) * 2
            });
        }, 500);

        return () => clearInterval(interval);
    }, [isAlive]);

    // Calculations
    const finalEyeScale = eyeOpenness * blinkState;

    // Coordinates (Base + User Offset)
    // Eye Y: 160 + 15 (Reference + Offset) = 175
    const leftEyeX = 110 + gazeX + jitter.x;
    const rightEyeX = 290 + gazeX + jitter.x;
    const eyeY = 175 + gazeY + jitter.y;

    const mouthXPos = 200 + (gazeX * 0.3) + jitter.x + mouthX;
    const mouthYPos = 260 + (gazeY * 0.3) + jitter.y + mouthY;

    // Mouth Shape (Base + User Offset)
    // Curve Base: 14, Openness Base: 29
    const finalMouthCurve = 14 + mouthCurve;
    const finalMouthOpenness = 29 + mouthOpenness;

    return (
        <div className="w-full h-full flex justify-center items-center">
            {/* 
                Face Container (Self-contained)
                - Black background and shape defined here
                - Visual styles: bg-black, rounded corners, shadow
            */}
            <motion.div
                className="relative w-full h-full bg-black rounded-[3rem] border border-white/5 shadow-2xl overflow-hidden flex items-center justify-center"
                animate={{
                    boxShadow: `0 0 ${20 + glowIntensity * 50}px ${color}15` // Dynamic outer glow
                }}
                transition={{ duration: 0.5 }}
                style={{ aspectRatio: '1/1' }}
            >
                {/* Inner Ambient Glow */}
                <div
                    className="absolute inset-0 opacity-20 pointer-events-none"
                    style={{ background: `radial-gradient(circle at 50% 50%, ${color}, transparent 70%)` }}
                />

                <svg
                    width="100%"
                    height="100%"
                    viewBox={`0 0 ${CANVAS_SIZE} ${CANVAS_SIZE}`}
                    preserveAspectRatio="xMidYMid meet"
                    className="overflow-visible w-full h-full"
                >
                    <Eye
                        x={leftEyeX}
                        y={eyeY}
                        width={100}
                        height={110}
                        scaleY={finalEyeScale}
                        squeeze={eyeSqueeze}
                        smile={eyeSmile}
                        color={color}
                        glowIntensity={glowIntensity}
                    />

                    <Eye
                        x={rightEyeX}
                        y={eyeY}
                        width={100}
                        height={110}
                        scaleY={finalEyeScale}
                        squeeze={eyeSqueeze}
                        smile={eyeSmile}
                        color={color}
                        glowIntensity={glowIntensity}
                    />

                    <Mouth
                        x={mouthXPos}
                        y={mouthYPos}
                        curve={finalMouthCurve}
                        openness={finalMouthOpenness}
                        color={color}
                        glowIntensity={glowIntensity}
                    />
                </svg>
            </motion.div>
        </div>
    );
};

export default FaceRenderer;