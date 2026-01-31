import React, { useState, useEffect } from 'react';
import Eye from './Eye';
import Mouth from './Mouth';
import { motion } from 'framer-motion';

const FaceRenderer = ({
    eyeOpenness = 1.0,  // 0.0 to 1.0
    mouthCurve = 0,     // -100 to 100
    mouthOpenness = 0,  // 0 to 100
    eyeSqueeze = 0,     // 0.0 to 1.0
    gazeX = 0,          // -50 to 50
    gazeY = 0,          // -50 to 50
    color = "#FFFFFF",
    glowIntensity = 0.5,
    isAlive = true      // Enable liveness (blinking, breathing)
}) => {
    const CANVAS_SIZE = 400;

    // -- Liveness State --
    const [blinkState, setBlinkState] = useState(1.0); // 1 = open, 0 = closed
    const [jitter, setJitter] = useState({ x: 0, y: 0 });

    // 1. Blinking Logic
    useEffect(() => {
        if (!isAlive) return;

        let timeout;
        const triggerBlink = () => {
            setBlinkState(0); // Close
            setTimeout(() => setBlinkState(1), 150); // Open after 150ms

            // Schedule next blink (Random interval between 2s and 6s)
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
            // Very small random movements
            setJitter({
                x: (Math.random() - 0.5) * 2, // +/- 1px
                y: (Math.random() - 0.5) * 2
            });
        }, 500);

        return () => clearInterval(interval);
    }, [isAlive]);

    // Calculate final eye scale (User input * Blink factor)
    // If eyeOpenness is 0 (closed by user), blink shouldn't open it.
    const finalEyeScale = eyeOpenness * blinkState;

    // Eye Positions (Base + Gaze + Jitter)
    // Left Eye Base: 110, 160
    // Right Eye Base: 290, 160
    const leftEyeX = 110 + gazeX + jitter.x;
    const rightEyeX = 290 + gazeX + jitter.x;
    const eyeY = 160 + gazeY + jitter.y;

    // Mouth Position (Base + Jitter)
    const mouthX = 200 + (gazeX * 0.3) + jitter.x; // Mouth moves less than eyes for 3D effect
    const mouthY = 280 + (gazeY * 0.3) + jitter.y;

    return (
        <div className="relative w-full h-full flex justify-center items-center debug-mode">
            {/* Glow Filter Definition Container (hidden) - Commented out for debugging
            <svg width="0" height="0">
                <defs>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="6" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>
            </svg>
            */}

            <motion.div
                className="w-[400px] h-[400px] bg-gray-800 rounded-[60px] border-4 border-white/20"
                animate={{
                    boxShadow: `0 0 ${20 + glowIntensity * 30}px ${color}33` // Hex opacity 33
                }}
                transition={{ duration: 0.5 }}
            >
                <svg
                    width="100%"
                    height="100%"
                    viewBox={`0 0 ${CANVAS_SIZE} ${CANVAS_SIZE}`}
                    className="overflow-visible"
                >
                    <Eye
                        x={leftEyeX}
                        y={eyeY}
                        scaleY={finalEyeScale}
                        squeeze={eyeSqueeze}
                        color={color}
                        glowIntensity={glowIntensity}
                    />

                    <Eye
                        x={rightEyeX}
                        y={eyeY}
                        scaleY={finalEyeScale}
                        squeeze={eyeSqueeze}
                        color={color}
                        glowIntensity={glowIntensity}
                    />

                    <Mouth
                        x={mouthX}
                        y={mouthY}
                        curve={mouthCurve}
                        openness={mouthOpenness}
                        color={color}
                        glowIntensity={glowIntensity}
                    />
                </svg>
            </motion.div>
        </div>
    );
};

export default FaceRenderer;
