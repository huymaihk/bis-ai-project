import React from 'react';
import { DepartmentId } from '../types/bisTypes';
import { RobotEyeStyle, RobotFinishPreset } from '../utils/agentOfficeSim';

interface AgentRobotAvatarProps {
  department: DepartmentId;
  size?: 'sm' | 'md' | 'lg';
  isActive?: boolean;
  hasAlert?: boolean;
  reduceMotion?: boolean;
  showDesk?: boolean;
  eyeStyle?: RobotEyeStyle;
  finishPreset?: RobotFinishPreset;
  customColorHex?: string;
}

const DEPT_PALETTES: Record<
  DepartmentId,
  {
    primary: string;
    highlight: string;
    midtone: string;
    shadow: string;
    rimLight: string;
    eyeColor: string;
    visorBorder: string;
  }
> = {
  overview: {
    primary: '#E11D48',
    highlight: '#FFE4E6',
    midtone: '#F43F5E',
    shadow: '#4C0519',
    rimLight: '#FB7185',
    eyeColor: '#FFFFFF',
    visorBorder: '#FDA4AF',
  },
  technical: {
    primary: '#F59E0B',
    highlight: '#FEF3C7',
    midtone: '#FBBF24',
    shadow: '#451A03',
    rimLight: '#FDE68A',
    eyeColor: '#FEF08A',
    visorBorder: '#FBBF24',
  },
  marketing: {
    primary: '#E2E8F0',
    highlight: '#FFFFFF',
    midtone: '#94A3B8',
    shadow: '#1E293B',
    rimLight: '#F8FAFC',
    eyeColor: '#38BDF8',
    visorBorder: '#CBD5E1',
  },
  imagestudio: {
    primary: '#0EA5E9',
    highlight: '#E0F2FE',
    midtone: '#38BDF8',
    shadow: '#082F49',
    rimLight: '#7DD3FC',
    eyeColor: '#7DD3FC',
    visorBorder: '#38BDF8',
  },
  operations: {
    primary: '#EF4444',
    highlight: '#FEE2E2',
    midtone: '#F87171',
    shadow: '#450A0A',
    rimLight: '#FCA5A5',
    eyeColor: '#FECACA',
    visorBorder: '#F87171',
  },
  knowledge: {
    primary: '#10B981',
    highlight: '#D1FAE5',
    midtone: '#34D399',
    shadow: '#022C22',
    rimLight: '#6EE7B7',
    eyeColor: '#A7F3D0',
    visorBorder: '#34D399',
  },
  memory: {
    primary: '#A855F7',
    highlight: '#F3E8FF',
    midtone: '#C084FC',
    shadow: '#3B0764',
    rimLight: '#D8B4FE',
    eyeColor: '#E9D5FF',
    visorBorder: '#C084FC',
  },
};

export const AgentRobotAvatar: React.FC<AgentRobotAvatarProps> = ({
  department,
  size = 'md',
  isActive = false,
  hasAlert = false,
  reduceMotion = false,
  showDesk = false,
  eyeStyle = 'rounded',
  finishPreset = 'anodized-metal',
}) => {
  const palette = DEPT_PALETTES[department] || DEPT_PALETTES.technical;
  const uid = React.useId().replace(/:/g, '');
  const bodyGradId = `robot3d-body-${uid}`;
  const headGradId = `robot3d-head-${uid}`;
  const clearcoatId = `robot3d-coat-${uid}`;
  const visorGlowId = `robot3d-visor-${uid}`;

  const dimensions =
    size === 'sm'
      ? 'w-10 h-10'
      : size === 'lg'
      ? 'w-24 h-24'
      : 'w-14 h-14';

  const specularOpacity =
    finishPreset === 'mirror-chrome'
      ? 0.95
      : finishPreset === 'matte-ceramic'
      ? 0.35
      : 0.78;

  const activeEyeColor = hasAlert ? '#FBBF24' : palette.eyeColor;

  return (
    <div
      className={`relative inline-flex items-center justify-center select-none ${dimensions} ${
        !reduceMotion && isActive
          ? 'transition-transform duration-300 -translate-y-0.5'
          : ''
      }`}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 110 116"
        className="w-full h-full overflow-visible"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* 3D Spherical/Anodized Metallic Gradient for Helmet */}
          <radialGradient id={headGradId} cx="32%" cy="24%" r="72%">
            <stop offset="0%" stopColor={palette.highlight} />
            <stop offset="28%" stopColor={palette.midtone} />
            <stop offset="68%" stopColor={palette.primary} />
            <stop offset="100%" stopColor={palette.shadow} />
          </radialGradient>

          {/* 3D Torso Metallic Gradient */}
          <linearGradient id={bodyGradId} x1="18%" y1="8%" x2="84%" y2="94%">
            <stop offset="0%" stopColor={palette.highlight} />
            <stop offset="35%" stopColor={palette.primary} />
            <stop offset="100%" stopColor={palette.shadow} />
          </linearGradient>

          {/* Glossy Clearcoat Studio Softbox Highlight */}
          <linearGradient id={clearcoatId} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop
              offset="0%"
              stopColor="#FFFFFF"
              stopOpacity={specularOpacity}
            />
            <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0" />
          </linearGradient>

          {/* Visor Inner Glow */}
          <radialGradient id={visorGlowId} cx="50%" cy="50%" r="55%">
            <stop offset="0%" stopColor="#1E293B" />
            <stop offset="100%" stopColor="#05070B" />
          </radialGradient>
        </defs>

        {/* Ground Contact Shadow */}
        <ellipse
          cx="55"
          cy="106"
          rx="32"
          ry="7"
          fill="#000000"
          fillOpacity="0.65"
        />
        {isActive && (
          <ellipse
            cx="55"
            cy="106"
            rx="26"
            ry="4.5"
            fill={palette.primary}
            fillOpacity="0.35"
          />
        )}

        {/* Articulated Left & Right Feet / Legs */}
        <rect
          x="37"
          y="86"
          width="14"
          height="16"
          rx="7"
          fill={`url(#${bodyGradId})`}
          stroke="#090B10"
          strokeWidth="1.5"
        />
        <rect
          x="59"
          y="86"
          width="14"
          height="16"
          rx="7"
          fill={`url(#${bodyGradId})`}
          stroke="#090B10"
          strokeWidth="1.5"
        />

        {/* Articulated Rounded Arms (Chubby SAMS 3D Proportions) */}
        <rect
          x="16"
          y="58"
          width="13"
          height="26"
          rx="6.5"
          transform="rotate(8 22 70)"
          fill={`url(#${bodyGradId})`}
          stroke="#090B10"
          strokeWidth="1.5"
        />
        <rect
          x="81"
          y="58"
          width="13"
          height="26"
          rx="6.5"
          transform="rotate(-8 87 70)"
          fill={`url(#${bodyGradId})`}
          stroke="#090B10"
          strokeWidth="1.5"
        />

        {/* Chubby 3D Torso */}
        <rect
          x="28"
          y="54"
          width="54"
          height="38"
          rx="18"
          fill={`url(#${bodyGradId})`}
          stroke="#090B10"
          strokeWidth="1.6"
        />
        {/* Torso Clearcoat Top Reflection */}
        <ellipse
          cx="55"
          cy="61"
          rx="20"
          ry="6"
          fill={`url(#${clearcoatId})`}
        />

        {/* Chest Core Telemetry Pill */}
        <rect
          x="44"
          y="68"
          width="22"
          height="10"
          rx="5"
          fill="#07090E"
          stroke={palette.visorBorder}
          strokeWidth="1.2"
        />
        <circle cx="50" cy="73" r="2" fill={activeEyeColor} />
        <rect
          x="55"
          y="71.5"
          width="7"
          height="3"
          rx="1.5"
          fill={palette.primary}
        />

        {/* 3D SAMS-Style Rounded Squircle Helmet Head */}
        <rect
          x="20"
          y="10"
          width="70"
          height="50"
          rx="20"
          fill={`url(#${headGradId})`}
          stroke={isActive ? '#FFFFFF' : '#090B10'}
          strokeWidth={isActive ? '2.2' : '1.6'}
        />

        {/* Studio Softbox Clearcoat Highlight on Crown */}
        <path
          d="M 33 15 Q 55 11 77 15 Q 68 23 42 23 Z"
          fill={`url(#${clearcoatId})`}
        />
        <ellipse
          cx="36"
          cy="20"
          rx="12"
          ry="4.5"
          transform="rotate(-12 36 20)"
          fill="#FFFFFF"
          fillOpacity={specularOpacity * 0.75}
        />

        {/* Recessed Black Glass Visor */}
        <rect
          x="28"
          y="21"
          width="54"
          height="30"
          rx="12"
          fill={`url(#${visorGlowId})`}
          stroke={palette.visorBorder}
          strokeWidth="1.6"
        />

        {/* Visor Diagonal Glass Sheen */}
        <path
          d="M 33 24 L 58 24 L 46 47 L 31 47 Z"
          fill="#FFFFFF"
          fillOpacity="0.09"
        />

        {/* Expressive Luminous Eyes (Supports Rounded, Focused, Happy, Wink) */}
        {eyeStyle === 'happy' ? (
          <>
            <path
              d="M 37 38 Q 43 29 49 38"
              stroke={activeEyeColor}
              strokeWidth="4"
              strokeLinecap="round"
              fill="none"
            />
            <path
              d="M 61 38 Q 67 29 73 38"
              stroke={activeEyeColor}
              strokeWidth="4"
              strokeLinecap="round"
              fill="none"
            />
          </>
        ) : eyeStyle === 'focused' ? (
          <>
            <rect
              x="36"
              y="32"
              width="13"
              height="7"
              rx="3"
              fill={activeEyeColor}
            />
            <rect
              x="61"
              y="32"
              width="13"
              height="7"
              rx="3"
              fill={activeEyeColor}
            />
          </>
        ) : eyeStyle === 'wink' ? (
          <>
            <rect
              x="37"
              y="29"
              width="11"
              height="14"
              rx="5.5"
              fill={activeEyeColor}
            />
            <circle cx="40.5" cy="33" r="2" fill="#FFFFFF" />
            <path
              d="M 61 36 Q 67 30 73 36"
              stroke={activeEyeColor}
              strokeWidth="3.5"
              strokeLinecap="round"
              fill="none"
            />
          </>
        ) : (
          <>
            <rect
              x="37"
              y="29"
              width="11"
              height="14"
              rx="5.5"
              fill={activeEyeColor}
            />
            <rect
              x="62"
              y="29"
              width="11"
              height="14"
              rx="5.5"
              fill={activeEyeColor}
            />
            <circle cx="40.5" cy="33" r="2" fill="#FFFFFF" />
            <circle cx="65.5" cy="33" r="2" fill="#FFFFFF" />
          </>
        )}

        {/* Optional Workstation Holo-Desk */}
        {showDesk && (
          <g>
            <path
              d="M 16 95 L 55 87 L 94 95 L 55 103 Z"
              fill="#181C26"
              stroke={palette.primary}
              strokeWidth="1.4"
            />
            <rect
              x="41"
              y="81"
              width="28"
              height="12"
              rx="3"
              fill="#0B0C0F"
              stroke={palette.visorBorder}
              strokeWidth="1.2"
            />
          </g>
        )}
      </svg>
    </div>
  );
};
