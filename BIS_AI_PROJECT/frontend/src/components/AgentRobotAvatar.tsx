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
    accentColor: string;
    earCupColor: string;
    eyeColor: string;
    visorBorder: string;
  }
> = {
  overview: {
    accentColor: '#D9382C',
    earCupColor: '#B91C1C',
    eyeColor: '#FF9E44',
    visorBorder: '#D4B89E',
  },
  technical: {
    accentColor: '#0EA5E9',
    earCupColor: '#0284C7',
    eyeColor: '#67E8F9',
    visorBorder: '#38BDF8',
  },
  marketing: {
    accentColor: '#B91C1C',
    earCupColor: '#991B1B',
    eyeColor: '#FF9E44',
    visorBorder: '#E5B49A',
  },
  imagestudio: {
    accentColor: '#E03B2F',
    earCupColor: '#B91C1C',
    eyeColor: '#FF9E44',
    visorBorder: '#F87171',
  },
  operations: {
    accentColor: '#10B981',
    earCupColor: '#B91C1C',
    eyeColor: '#67E8F9',
    visorBorder: '#6EE7B7',
  },
  knowledge: {
    accentColor: '#D97706',
    earCupColor: '#92400E',
    eyeColor: '#FF9E44',
    visorBorder: '#F59E0B',
  },
  memory: {
    accentColor: '#F59E0B',
    earCupColor: '#B45309',
    eyeColor: '#FF9E44',
    visorBorder: '#FBBF24',
  },
};

export const AgentRobotAvatar: React.FC<AgentRobotAvatarProps> = ({
  department,
  size = 'md',
  isActive = false,
  hasAlert = false,
  reduceMotion = false,
  eyeStyle = 'rounded',
  finishPreset = 'anodized-metal',
}) => {
  const palette = DEPT_PALETTES[department] || DEPT_PALETTES.overview;
  const uid = React.useId().replace(/:/g, '');
  const bodyGradId = `bisrobot-body-${uid}`;
  const headGradId = `bisrobot-head-${uid}`;
  const chromeGradId = `bisrobot-chrome-${uid}`;
  const gunmetalGradId = `bisrobot-gunmetal-${uid}`;
  const visorGlowId = `bisrobot-visor-${uid}`;

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
      ? 0.45
      : 0.85;

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
        viewBox="0 0 110 118"
        className="w-full h-full overflow-visible"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Brushed Titanium-Alloy Metallic Helmet Gradient */}
          <linearGradient id={headGradId} x1="12%" y1="8%" x2="88%" y2="92%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="22%" stopColor="#E6E1DA" />
            <stop offset="52%" stopColor="#C4B8AC" />
            <stop offset="78%" stopColor="#8B7C70" />
            <stop offset="100%" stopColor="#4A3F37" />
          </linearGradient>

          {/* Machined Titanium Torso Armor Gradient */}
          <linearGradient id={bodyGradId} x1="15%" y1="5%" x2="85%" y2="95%">
            <stop offset="0%" stopColor="#F8F6F2" />
            <stop offset="30%" stopColor="#D6CCC0" />
            <stop offset="68%" stopColor="#9C8D7E" />
            <stop offset="100%" stopColor="#52453C" />
          </linearGradient>

          {/* Mirror-Chrome Hydraulic Joint Gradient */}
          <linearGradient id={chromeGradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="40%" stopColor="#CBD5E1" />
            <stop offset="65%" stopColor="#475569" />
            <stop offset="100%" stopColor="#F1F5F9" />
          </linearGradient>

          {/* CNC Dark Gunmetal Endoskeleton Gradient */}
          <linearGradient id={gunmetalGradId} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#475569" />
            <stop offset="50%" stopColor="#1E293B" />
            <stop offset="100%" stopColor="#0F172A" />
          </linearGradient>

          {/* Deep Optical Smoked Glass Visor */}
          <radialGradient id={visorGlowId} cx="50%" cy="50%" r="58%">
            <stop offset="0%" stopColor="#1F1916" />
            <stop offset="100%" stopColor="#080605" />
          </radialGradient>
        </defs>

        {/* Ground Contact Shadow */}
        <ellipse
          cx="55"
          cy="109"
          rx="32"
          ry="5.5"
          fill="#000000"
          fillOpacity="0.58"
        />

        {/* Articulated Gunmetal Hip Pistons & Magnetic-Clamp Metallic Boots */}
        <rect
          x="39"
          y="85"
          width="9"
          height="10"
          rx="2"
          fill={`url(#${gunmetalGradId})`}
          stroke="#94A3B8"
          strokeWidth="0.9"
        />
        <rect
          x="62"
          y="85"
          width="9"
          height="10"
          rx="2"
          fill={`url(#${gunmetalGradId})`}
          stroke="#94A3B8"
          strokeWidth="0.9"
        />
        <rect
          x="35"
          y="93"
          width="16"
          height="13"
          rx="4"
          fill={`url(#${bodyGradId})`}
          stroke="#27201C"
          strokeWidth="1.5"
        />
        <rect
          x="59"
          y="93"
          width="16"
          height="13"
          rx="4"
          fill={`url(#${bodyGradId})`}
          stroke="#27201C"
          strokeWidth="1.5"
        />
        {/* Crimson Anodized Boot Toe Caps */}
        <rect x="37" y="101" width="12" height="4" rx="1.5" fill={palette.accentColor} />
        <rect x="61" y="101" width="12" height="4" rx="1.5" fill={palette.accentColor} />

        {/* Gunmetal Ribbed Neck & Waist Spine */}
        <rect
          x="45"
          y="53"
          width="20"
          height="9"
          rx="3"
          fill={`url(#${gunmetalGradId})`}
          stroke="#94A3B8"
          strokeWidth="1"
        />

        {/* Articulated Shoulder Ball-Joints & Metallic Arms */}
        <circle
          cx="25"
          cy="64"
          r="6"
          fill={`url(#${chromeGradId})`}
          stroke="#1E293B"
          strokeWidth="1.2"
        />
        <circle
          cx="85"
          cy="64"
          r="6"
          fill={`url(#${chromeGradId})`}
          stroke="#1E293B"
          strokeWidth="1.2"
        />
        <rect
          x="15"
          y="63"
          width="12"
          height="23"
          rx="5"
          transform="rotate(7 21 73)"
          fill={`url(#${bodyGradId})`}
          stroke="#27201C"
          strokeWidth="1.5"
        />
        <rect
          x="83"
          y="63"
          width="12"
          height="23"
          rx="5"
          transform="rotate(-7 89 73)"
          fill={`url(#${bodyGradId})`}
          stroke="#27201C"
          strokeWidth="1.5"
        />

        {/* CNC-Machined Titanium Chest Cuirass */}
        <rect
          x="28"
          y="58"
          width="54"
          height="32"
          rx="11"
          fill={`url(#${bodyGradId})`}
          stroke="#27201C"
          strokeWidth="1.6"
        />
        {/* Metallic Chest Panel Seam & Specular Bevel */}
        <rect
          x="33"
          y="62"
          width="44"
          height="24"
          rx="7"
          fill="none"
          stroke="#FFFFFF"
          strokeOpacity="0.45"
          strokeWidth="1"
        />

        {/* Anodized Department Chest V-Trim & Core */}
        <path
          d="M 39 60 L 55 74 L 71 60"
          stroke={palette.accentColor}
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle
          cx="55"
          cy="79"
          r="4.5"
          fill={activeEyeColor}
          stroke={`url(#${chromeGradId})`}
          strokeWidth="1.5"
        />

        {/* Acoustic Side Servo Ear-Pods with Chrome Bezels */}
        <rect
          x="12"
          y="26"
          width="9"
          height="21"
          rx="4"
          fill={palette.earCupColor}
          stroke={`url(#${chromeGradId})`}
          strokeWidth="1.5"
        />
        <rect
          x="89"
          y="26"
          width="9"
          height="21"
          rx="4"
          fill={palette.earCupColor}
          stroke={`url(#${chromeGradId})`}
          strokeWidth="1.5"
        />

        {/* Image Studio Red Headphone Arc */}
        {department === 'imagestudio' && (
          <path
            d="M 17 29 C 17 3, 93 3, 93 29"
            stroke="#D9382C"
            strokeWidth="4.5"
            strokeLinecap="round"
            fill="none"
          />
        )}

        {/* Chamfered Brushed-Titanium Helmet Shell */}
        <rect
          x="19"
          y="11"
          width="72"
          height="48"
          rx="18"
          fill={`url(#${headGradId})`}
          stroke={isActive ? '#F59E0B' : '#27201C'}
          strokeWidth={isActive ? '2.2' : '1.6'}
        />

        {/* Machined Panel Seam Lines & Hex Rivets on Helmet */}
        <line
          x1="32"
          y1="12"
          x2="36"
          y2="22"
          stroke="#3E332B"
          strokeOpacity="0.55"
          strokeWidth="1.1"
        />
        <line
          x1="78"
          y1="12"
          x2="74"
          y2="22"
          stroke="#3E332B"
          strokeOpacity="0.55"
          strokeWidth="1.1"
        />
        <circle cx="26" cy="19" r="1.4" fill="#475569" />
        <circle cx="84" cy="19" r="1.4" fill="#475569" />

        {/* Anisotropic Metallic Crown Specular Highlight */}
        <ellipse
          cx="44"
          cy="17.5"
          rx="16"
          ry="3.5"
          fill="#FFFFFF"
          fillOpacity={specularOpacity}
        />

        {/* Red Anodized "BIS" Forehead Badge */}
        <rect
          x="44"
          y="14.5"
          width="22"
          height="5.5"
          rx="2.5"
          fill="#D9382C"
          stroke="#FDE68A"
          strokeWidth="0.7"
        />

        {/* Recessed Smoked Optical Visor with Chrome Outer Bezel */}
        <rect
          x="25.5"
          y="22"
          width="59"
          height="30"
          rx="12"
          fill={`url(#${visorGlowId})`}
          stroke={`url(#${chromeGradId})`}
          strokeWidth="2.2"
        />

        {/* Precision Optical LED Eye Lenses with Metallic Aperture Rings */}
        {eyeStyle === 'happy' ? (
          <>
            <path
              d="M 36 39 Q 42 30 48 39"
              stroke={activeEyeColor}
              strokeWidth="4"
              strokeLinecap="round"
              fill="none"
            />
            <path
              d="M 62 39 Q 68 30 74 39"
              stroke={activeEyeColor}
              strokeWidth="4"
              strokeLinecap="round"
              fill="none"
            />
          </>
        ) : eyeStyle === 'focused' ? (
          <>
            <rect
              x="35"
              y="33.5"
              width="14"
              height="7.5"
              rx="3.5"
              fill={activeEyeColor}
              stroke="#FFFFFF"
              strokeWidth="0.8"
            />
            <rect
              x="61"
              y="33.5"
              width="14"
              height="7.5"
              rx="3.5"
              fill={activeEyeColor}
              stroke="#FFFFFF"
              strokeWidth="0.8"
            />
          </>
        ) : eyeStyle === 'wink' ? (
          <>
            <circle
              cx="42"
              cy="37"
              r="7.5"
              fill="none"
              stroke="#64748B"
              strokeWidth="1.4"
            />
            <circle cx="42" cy="37" r="6" fill={activeEyeColor} />
            <circle cx="40" cy="35" r="2" fill="#FFFFFF" />
            <path
              d="M 62 37 Q 68 31 74 37"
              stroke={activeEyeColor}
              strokeWidth="3.5"
              strokeLinecap="round"
              fill="none"
            />
          </>
        ) : (
          <>
            <circle
              cx="42"
              cy="37"
              r="7.8"
              fill="none"
              stroke="#64748B"
              strokeWidth="1.4"
            />
            <circle
              cx="68"
              cy="37"
              r="7.8"
              fill="none"
              stroke="#64748B"
              strokeWidth="1.4"
            />
            <circle cx="42" cy="37" r="6" fill={activeEyeColor} />
            <circle cx="68" cy="37" r="6" fill={activeEyeColor} />
            <circle cx="40" cy="34.8" r="2" fill="#FFFFFF" />
            <circle cx="66" cy="34.8" r="2" fill="#FFFFFF" />
          </>
        )}

        {/* Role Accessories: Marketing Red Beret, Knowledge Graduation Cap & Gold Glasses, Operations Cap */}
        {department === 'marketing' && (
          <path
            d="M 24 16 C 26 3, 70 3, 78 14 C 62 11, 36 12, 24 16 Z"
            fill="#B91C1C"
            stroke="#FDE68A"
            strokeWidth="1.1"
          />
        )}

        {department === 'knowledge' && (
          <>
            <polygon
              points="55,1 90,10 55,18 20,10"
              fill="#1E293B"
              stroke="#F59E0B"
              strokeWidth="1.3"
            />
            <line
              x1="78"
              y1="13"
              x2="82"
              y2="25"
              stroke="#F59E0B"
              strokeWidth="2"
            />
            <circle
              cx="42"
              cy="37"
              r="9.8"
              stroke="#F59E0B"
              strokeWidth="1.8"
              fill="none"
            />
            <circle
              cx="68"
              cy="37"
              r="9.8"
              stroke="#F59E0B"
              strokeWidth="1.8"
              fill="none"
            />
            <line
              x1="51.8"
              y1="37"
              x2="58.2"
              y2="37"
              stroke="#F59E0B"
              strokeWidth="1.8"
            />
          </>
        )}

        {department === 'operations' && (
          <path
            d="M 26 15 Q 55 6 84 15 L 89 20 Q 55 14 21 20 Z"
            fill="#1E293B"
            stroke="#D9382C"
            strokeWidth="1.3"
          />
        )}
      </svg>
    </div>
  );
};
