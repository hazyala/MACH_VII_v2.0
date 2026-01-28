import React from 'react';

const FaceRenderer = ({ expression }) => {
    // Note: expression is "safeExpr" (normalized) from parent or needs normalization here?
    // CenterPanel passes raw engine output. engine output has standard structure.

    const safeExpr = expression || {};
    // Engine structure: { leftEye: {openness}, rightEye: {openness}, happiness, etc. }
    // Or { eye: {openness...} } ? 
    // Check ExpressionEngine.js logic to be sure. 
    // Actually in previous step App.jsx used: engineRef.current.current which has { leftEye:..., rightEye:..., happiness... } usually if it's based on previous context.
    // BUT the previous FileRenderer code used { eye: {openness...}, mouth: ... }
    // Let's assume the Engine produces flattened or structured data.
    // To be safe, I'll support both or check the keys.
    // Looking at CenterPanel.jsx -> engineRef.current.update() returns object.
    // Let's implement a generic renderer that maps these.

    // Default values if missing
    const leftOpen = (safeExpr.leftEye?.openness ?? safeExpr.eye?.openness ?? 1.0);
    const rightOpen = (safeExpr.rightEye?.openness ?? safeExpr.eye?.openness ?? 1.0);
    const happiness = (safeExpr.happiness ?? safeExpr.mouth?.smile ?? 0.0);
    const roll = (safeExpr.head?.roll ?? 0.0);

    // Colors
    const faceColor = "#1D1D1F"; // Dark Gray/Black for features

    return (
        <div className="w-full h-full flex items-center justify-center">
            <svg
                width="100%"
                height="100%"
                viewBox="0 0 200 200"
                style={{ overflow: 'visible' }}
            >
                {/* Global Transform */}
                <g transform={`rotate(${roll}, 100, 100)`}>

                    {/* Eyes Group: Centered at 100, 80 */}
                    {/* Left Eye: -30 from center */}
                    <g transform="translate(70, 80)">
                        <ellipse
                            cx="0" cy="0"
                            rx="12" ry={15 * leftOpen}
                            fill={faceColor}
                        />
                        {/* Highlight */}
                        <circle cx="3" cy="-4" r="3" fill="white" opacity="0.2" />
                    </g>

                    {/* Right Eye: +30 from center */}
                    <g transform="translate(130, 80)">
                        <ellipse
                            cx="0" cy="0"
                            rx="12" ry={15 * rightOpen}
                            fill={faceColor}
                        />
                        <circle cx="3" cy="-4" r="3" fill="white" opacity="0.2" />
                    </g>

                    {/* Mouth: Centered at 100, 130 */}
                    {/* Simpler Smile Path */}
                    {/* M startX startY Q controlX controlY endX endY */}
                    <path
                        d={`M 70 120 Q 100 ${120 + (happiness * 20)} 130 120`}
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

// Memoize for performance
export default React.memo(FaceRenderer);
