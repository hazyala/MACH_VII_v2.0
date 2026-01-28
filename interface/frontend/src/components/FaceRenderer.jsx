const FaceRenderer = ({ expression }) => {
    // expression: { eye: {...}, mouth: {...}, head: {...} }
    // If expression is undefined, provide safe defaults
    const safeExpr = expression || {};

    // Deep Merge / Defaulting
    const eye = safeExpr.eye || { openness: 1.0, squint: 0.0, blink: 0.0, gazeX: 0.0, gazeY: 0.0 };
    const mouth = safeExpr.mouth || { openness: 0.0, smile: 0.0, width: 0.5 };
    const head = safeExpr.head || { tilt: 0.0, bob: 0.0 };

    // 1. Eye Calculation
    // Blink overrides openness
    const currentOpenness = (eye.openness * (1.0 - eye.blink)) * 100;
    const baseEyeW = 100;
    const baseEyeH = 120; // Slightly taller base
    const currEyeH = baseEyeH * (currentOpenness / 100.0);
    const eyeY = 160 - (currEyeH / 2);

    // Squint affects bottom eyelid (simplified as just height reduction from bottom?)
    // Or we can use path for complex eye shape. For MVP rect with rounded corners.
    // Squinting makes eyes wider but shorter? 
    // Let's standard: Squint reduces height further
    const squintFactor = 1.0 - (eye.squint * 0.4);
    const finalEyeH = currEyeH * squintFactor;
    const finalEyeY = 160 - (finalEyeH / 2);

    // Gaze Shift (Restricted to ±5px inside eye mostly, but user said +/- 3~5px)
    // Actually if we move the whole eye group, 30px is too much for "inside".
    // User said: "gazeX/Y는 눈 내부에서만 ±3~5px 범위로 제한하십시오."
    // This implies pupil movement OR slight eye shift. 
    // Since we are moving the whole eye rect (EMO style often moves the whole eye on screen),
    // but user specifically requested limitation. I will set it to 10px max for now to be safe but visible.
    // Wait, user said "Restrict to +/- 3~5px". I will follow strictly.
    const gazeOffsetX = eye.gazeX * 5;
    const gazeOffsetY = eye.gazeY * 5;

    // 2. Mouth Calculation
    // Smile (-1 to 1) -> Curve
    // Width (0 to 1) -> X spread
    const mouthWidth = 60 + (mouth.width * 100); // 60px to 160px
    const mouthCurve = mouth.smile * 60; // -60 (Frown) to +60 (Smile)

    const mouthCx = 200; // Center X
    const mouthCy = 200 + (mouth.openness * 30); // Raised to 200 to accommodate stroke/glow without clipping

    // ...

    return (
        // Removed overflow-hidden to allow glow effects to spill over slightly if needed, 
        // essentially satisfying "visual integrity" over strict bounding box clipping.
        // Actually, if we use SVG viewBox="0 0 400 400", it clips anyway unless style overflow is visible.
        <div className="flex items-center justify-center w-[400px] h-[400px] bg-[#050505] rounded-[40px] shadow-2xl relative border border-gray-800">
            <svg width="400" height="400" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style={{ overflow: 'visible' }}>
                <defs>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="6" result="coloredBlur" />
                        <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
                    </filter>
                </defs>

                {/* Face Root: The ONLY group ExpressionEngine should conceptually manipulate via state */}
                <g id="face-root" style={{ transform: `rotate(${tiltDeg}deg)`, transformOrigin: '200px 200px', transition: 'transform 0.1s ease-out' }}>

                    {/* Eye Group (Gaze) */}
                    <g style={{ transform: `translate(${gazeOffsetX}px, ${gazeOffsetY}px)`, transition: 'transform 0.05s linear' }}>
                        {/* Eyes only (No Brows) */}
                        {/* Left Eye: x=60, default width=100. Center ~110 */}
                        <rect x="60" y={finalEyeY} width={baseEyeW} height={finalEyeH} rx="20" ry="20" fill={eyeColor} filter="url(#glow)" />

                        {/* Right Eye: x=240, default width=100. Center ~290 */}
                        <rect x="240" y={finalEyeY} width={baseEyeW} height={finalEyeH} rx="20" ry="20" fill={eyeColor} filter="url(#glow)" />
                    </g>

                    {/* Mouth */}
                    <path d={`M ${mouthSx} ${mouthCy} Q ${mouthCx} ${controlY} ${mouthEx} ${mouthCy}`}
                        stroke={eyeColor} strokeWidth="8" fill="none" strokeLinecap="round" filter="url(#glow)"
                        opacity={0.8} />
                </g>
            </svg>
        </div>
    );
};

export default FaceRenderer;
