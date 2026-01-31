import { motion } from 'framer-motion';

const Eye = ({
    x = 0,
    y = 0,
    scaleY = 1,
    squeeze = 0, // 0 to 1 (1 = fully squeezed/happy)
    width = 100,
    height = 110,
    color = "#FFFFFF",
    glowIntensity = 0.5
}) => {
    // Calculate final dimensions based on state
    // When squeezed (smile), height decreases and width increases slightly
    const currentHeight = height * scaleY * (1 - squeeze * 0.5);
    const currentWidth = width + (squeeze * 20);

    // Radius changes: Squeezed eyes become flatter
    const radius = squeeze > 0.5 ? 20 : (scaleY < 0.3 ? 5 : 40);

    return (
        <motion.rect
            x={x - currentWidth / 2}
            y={y - currentHeight / 2}
            width={currentWidth}
            height={currentHeight}
            rx={radius}
            ry={radius}
            fill={color}

            // Framer Motion Animation
            animate={{
                x: x - currentWidth / 2,
                y: y - currentHeight / 2,
                width: currentWidth,
                height: currentHeight,
                rx: radius,
                ry: radius
            }}
            transition={{
                type: "spring",
                stiffness: 300,
                damping: 30
            }}

            style={{
                filter: `drop-shadow(0 0 ${glowIntensity * 20}px ${color})`
            }}
        />
    );
};

export default Eye;
