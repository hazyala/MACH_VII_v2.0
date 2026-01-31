import { motion } from 'framer-motion';

const Eye = ({
    x = 0,
    y = 0,
    scaleY = 1,
    squeeze = 0, // 0 to 1 (1 = fully squeezed/happy)
    smile = 0,   // 0 to 1 (1 = fully smiling eyes)
    width = 100,
    height = 110,
    color = "#FFFFFF",
    glowIntensity = 0.5
}) => {
    // Basic dimensions
    const baseWidth = width + (squeeze * 20);
    const baseHeight = height * (1 - squeeze * 0.5);
    const r = squeeze > 0.5 ? 20 : (scaleY < 0.3 ? 5 : 40);

    // Path Logic for "Smiling Eyes"
    // We define the corners of the eye
    const w2 = baseWidth / 2;
    const h2 = baseHeight / 2;

    // Normal Rounded Rect Path (Approximated with Q)
    const normalPath = `
        M ${-w2 + r}, ${-h2} 
        L ${w2 - r}, ${-h2} 
        Q ${w2}, ${-h2} ${w2}, ${-h2 + r} 
        L ${w2}, ${h2 - r} 
        Q ${w2}, ${h2} ${w2 - r}, ${h2} 
        L ${-w2 + r}, ${h2} 
        Q ${-w2}, ${h2} ${-w2}, ${h2 - r} 
        L ${-w2}, ${-h2 + r} 
        Q ${-w2}, ${-h2} ${-w2 + r}, ${-h2} 
        Z
    `.replace(/\s+/g, ' ');

    // Smiling Eye Path (Bottom curves up)
    // The bottom edge (L -w2+r, h2) is replaced by a Q toward the center
    const smilePath = `
        M ${-w2 + r}, ${-h2} 
        L ${w2 - r}, ${-h2} 
        Q ${w2}, ${-h2} ${w2}, ${-h2 + r} 
        L ${w2}, ${h2 - r - smile * h2} 
        Q ${0}, ${h2 - r - smile * height} ${-w2}, ${h2 - r - smile * h2} 
        L ${-w2}, ${-h2 + r} 
        Q ${-w2}, ${-h2} ${-w2 + r}, ${-h2} 
        Z
    `.replace(/\s+/g, ' ');

    return (
        <motion.g
            initial={false}
            animate={{ x, y }}
            transition={{
                type: "spring",
                stiffness: 400,
                damping: 40
            }}
        >
            <motion.path
                d={smile > 0 ? smilePath : normalPath}
                fill={color}
                animate={{
                    d: smile > 0 ? smilePath : normalPath,
                    scaleY: scaleY,
                }}
                transition={{
                    type: "spring",
                    stiffness: 400,
                    damping: 40
                }}
                style={{
                    transformOrigin: 'center',
                    transformBox: 'fill-box',
                    filter: `drop-shadow(0 0 ${glowIntensity * 20}px ${color})`
                }}
            />
        </motion.g>
    );
};

export default Eye;
