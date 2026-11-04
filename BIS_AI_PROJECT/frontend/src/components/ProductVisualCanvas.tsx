import React from 'react';
import { BisBackgroundId } from '../types/bisTypes';

interface ProductVisualCanvasProps {
  sku: string;
  variant:
    | 'pdf-scan-front'
    | 'pdf-scan-detail'
    | 'web-front-clean'
    | 'web-angle'
    | 'upload-raw'
    | 'bis-reference';
  backgroundId?: BisBackgroundId;
  paddingPercent?: number;
  shadowIntensity?: number;
  contrastBoost?: boolean;
  showGrid1254?: boolean;
  zoomScale?: number;
  className?: string;
}

const BG_STYLES: Record<BisBackgroundId, string> = {
  'bis-pure-white': 'bg-[#FFFFFF]',
  'bis-lab-neutral': 'bg-[#F3F4F6]',
  'bis-warm-ivory': 'bg-[#F8F6F0]',
  'bis-transparent': 'studio-checkerboard',
};

export const ProductVisualCanvas: React.FC<ProductVisualCanvasProps> = ({
  sku,
  variant,
  backgroundId = 'bis-pure-white',
  paddingPercent = 10,
  shadowIntensity = 15,
  contrastBoost = false,
  showGrid1254 = false,
  zoomScale = 1,
  className = '',
}) => {
  // Determine surface background based on whether it's raw source or processed studio
  const isRawPdf = variant === 'pdf-scan-front' || variant === 'pdf-scan-detail';
  const isRawUpload = variant === 'upload-raw';

  const containerBg = isRawPdf
    ? 'bg-[#F4EFE6]'
    : isRawUpload
    ? 'bg-[#DDE2E8]'
    : BG_STYLES[backgroundId];

  const innerScale = Math.max(0.65, 1 - (paddingPercent - 8) * 0.015) * zoomScale;

  return (
    <div
      className={`relative overflow-hidden select-none flex items-center justify-center ${containerBg} ${
        contrastBoost ? 'contrast-110' : ''
      } ${className}`}
    >
      {/* Raw PDF Catalogue Scan Overlay Artifacts */}
      {isRawPdf && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-2.5 left-3 right-3 flex justify-between text-[10px] font-mono text-[#78716C] border-b border-[#D6D0C4] pb-1">
            <span>CATALOGUE EXTRACT · {sku}</span>
            <span>300 DPI CMYK SCAN</span>
          </div>
          {/* Callout Leader Lines typical of PDF technical drawings */}
          <div className="absolute bottom-3 left-3 text-[10px] font-mono text-[#57534E] bg-[#EAE3D5] px-2 py-0.5 rounded border border-[#C7BFAFFF]">
            Fig 2.1 — Uncropped Source Frame
          </div>
        </div>
      )}

      {/* Raw Showroom Upload Clutter Simulation */}
      {isRawUpload && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-x-0 bottom-0 h-1/3 bg-[#BAC2CC] border-t border-[#94A3B8]" />
          <div className="absolute top-2.5 left-3 text-[10px] font-mono text-[#334155] bg-white/80 px-2 py-0.5 rounded">
            RAW_IMG_4092.JPG · Nền phòng Lab chưa tách
          </div>
        </div>
      )}

      {/* 1254 × 1254 Safe Margin & Center Crosshair Overlay */}
      {showGrid1254 && (
        <div className="absolute inset-0 pointer-events-none z-20">
          {/* Outer 8% Safe Margin Box */}
          <div
            className="absolute border border-dashed border-[#0EA5E9]/70"
            style={{
              inset: `${paddingPercent}%`,
            }}
          />
          {/* Center Hairlines */}
          <div className="absolute inset-y-0 left-1/2 w-px bg-[#0EA5E9]/25" />
          <div className="absolute inset-x-0 top-1/2 h-px bg-[#0EA5E9]/25" />
          <div className="absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-mono bg-[#0B0C0F]/85 text-[#38BDF8] rounded border border-[#0EA5E9]/40 tabular-nums">
            1254 × 1254 px · Safe Margin {paddingPercent}%
          </div>
        </div>
      )}

      {/* Precision SVG Instrument Illustration */}
      <div
        className="w-full h-full flex items-center justify-center transition-transform duration-200"
        style={{
          transform: `scale(${innerScale})`,
        }}
      >
        <svg
          viewBox="0 0 400 400"
          className="w-4/5 h-4/5 max-w-[340px] max-h-[340px]"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Studio Ground Shadow */}
          <ellipse
            cx="200"
            cy="342"
            rx="135"
            ry="18"
            fill="#0F172A"
            fillOpacity={Math.min(0.45, shadowIntensity / 60)}
          />

          {(sku === '03026A' || sku === '03026') && (
            <g>
              {/* Lab Background Wall & Subtle Grid when in Reference or Clean Mode */}
              <rect x="44" y="34" width="312" height="304" rx="12" fill="#EAE4DC" fillOpacity="0.45" />
              {/* Twin-Column Base Cabinet */}
              <rect
                x="78"
                y="278"
                width="210"
                height="58"
                rx="6"
                fill="#475569"
                stroke="#1E293B"
                strokeWidth="3"
              />
              <rect
                x="84"
                y="284"
                width="198"
                height="38"
                rx="4"
                fill="#CBD5E1"
                stroke="#475569"
                strokeWidth="1.5"
              />
              {/* Red BIS Bottom Accent Bar */}
              <rect x="78" y="328" width="210" height="6" rx="2" fill="#E03B2F" />
              {/* BIS Brand Logo on Base */}
              <text
                x="162"
                y="309"
                fill="#1E293B"
                fontSize="16"
                fontFamily="sans-serif"
                fontWeight="900"
                letterSpacing="1"
              >
                BIS
              </text>

              {/* Left & Right Twin Load Columns */}
              <rect
                x="102"
                y="62"
                width="24"
                height="218"
                fill="#E2E8F0"
                stroke="#334155"
                strokeWidth="2.5"
              />
              <rect
                x="111"
                y="64"
                width="6"
                height="214"
                fill="#94A3B8"
              />
              <rect
                x="240"
                y="62"
                width="24"
                height="218"
                fill="#E2E8F0"
                stroke="#334155"
                strokeWidth="2.5"
              />
              <rect
                x="249"
                y="64"
                width="6"
                height="214"
                fill="#94A3B8"
              />

              {/* Top Fixed Crown Beam */}
              <rect
                x="94"
                y="46"
                width="178"
                height="22"
                rx="4"
                fill="#334155"
                stroke="#0F172A"
                strokeWidth="2.5"
              />
              <text
                x="148"
                y="60"
                fill="#F8FAFC"
                fontSize="9"
                fontFamily="monospace"
                fontWeight="bold"
              >
                BIS · {sku}
              </text>

              {/* Moving Servo Crosshead Beam & 50kN Load Cell */}
              <rect
                x="98"
                y="132"
                width="170"
                height="26"
                rx="4"
                fill="#475569"
                stroke="#1E293B"
                strokeWidth="2.5"
              />
              <rect x="104" y="142" width="158" height="6" fill="#E03B2F" />
              {/* Loadcell Cylinder */}
              <rect
                x="167"
                y="158"
                width="32"
                height="18"
                rx="3"
                fill="#94A3B8"
                stroke="#334155"
                strokeWidth="2"
              />

              {/* Upper & Lower Pneumatic Specimen Grips (Clamps) */}
              <path
                d="M161 176H205L199 198H167L161 176Z"
                fill="#334155"
                stroke="#0F172A"
                strokeWidth="2"
              />
              <path
                d="M167 242H199L205 264H161L167 242Z"
                fill="#334155"
                stroke="#0F172A"
                strokeWidth="2"
              />
              <rect x="175" y="264" width="16" height="16" fill="#475569" />

              {/* Stretched Textile Strip Specimen (ISO 13934-1) between Jaws */}
              <rect
                x="174"
                y="196"
                width="18"
                height="48"
                fill="#B91C1C"
                stroke="#7F1D1D"
                strokeWidth="1.5"
              />
              <line x1="178" y1="196" x2="178" y2="244" stroke="#FCA5A5" strokeWidth="1" strokeDasharray="2 2" />
              <line x1="188" y1="196" x2="188" y2="244" stroke="#FCA5A5" strokeWidth="1" strokeDasharray="2 2" />

              {/* Side Digital Control Unit & Touchscreen */}
              <rect
                x="264"
                y="156"
                width="26"
                height="10"
                fill="#475569"
              />
              <rect
                x="284"
                y="128"
                width="62"
                height="96"
                rx="6"
                fill="#F8FAFC"
                stroke="#334155"
                strokeWidth="2.5"
              />
              <rect
                x="291"
                y="136"
                width="48"
                height="42"
                rx="3"
                fill="#0F172A"
              />
              {/* Stress-Strain Curve on Screen */}
              <path
                d="M295 172 Q 308 145 332 142"
                stroke="#38BDF8"
                strokeWidth="2"
                fill="none"
              />
              <text x="295" y="150" fill="#4ADE80" fontSize="7" fontFamily="monospace">
                50.0 kN
              </text>
              {/* Control Keypad */}
              <circle cx="303" cy="192" r="5" fill="#10B981" />
              <circle cx="316" cy="192" r="5" fill="#F59E0B" />
              <circle cx="329" cy="192" r="6" fill="#E03B2F" />
              <rect x="294" y="205" width="42" height="10" rx="2" fill="#CBD5E1" />
            </g>
          )}

          {sku === 'JH-M235-9' && (
            <g>
              {/* Base Chassis of Martindale 9-Station M235 */}
              <path
                d="M58 265L82 215H318L342 265V325C342 332 336 338 328 338H72C64 338 58 332 58 325V265Z"
                fill="#F8FAFC"
                stroke="#334155"
                strokeWidth="3"
              />
              {/* Front Beveled Fascia */}
              <rect
                x="64"
                y="268"
                width="272"
                height="62"
                rx="6"
                fill="#E2E8F0"
                stroke="#475569"
                strokeWidth="2"
              />
              {/* James Heal Signature Crimson & Navy Brand Strip */}
              <rect x="76" y="280" width="96" height="38" rx="4" fill="#0F172A" />
              <rect x="76" y="280" width="8" height="38" rx="2" fill="#E11D48" />
              <text
                x="92"
                y="296"
                fill="#FFFFFF"
                fontSize="9"
                fontFamily="monospace"
                fontWeight="bold"
              >
                JAMES HEAL
              </text>
              <text
                x="92"
                y="310"
                fill="#38BDF8"
                fontSize="8"
                fontFamily="monospace"
              >
                MARTINDALE M235
              </text>

              {/* Central Touchscreen Display */}
              <rect
                x="186"
                y="276"
                width="88"
                height="46"
                rx="4"
                fill="#090D16"
                stroke="#64748B"
                strokeWidth="2"
              />
              <text
                x="196"
                y="294"
                fill="#38BDF8"
                fontSize="8"
                fontFamily="monospace"
              >
                ISO 12947-2
              </text>
              <text
                x="196"
                y="310"
                fill="#F8FAFC"
                fontSize="11"
                fontFamily="monospace"
                fontWeight="bold"
              >
                50,000 CYC
              </text>

              {/* Emergency Stop & Start Controls */}
              <circle cx="305" cy="299" r="13" fill="#FACC15" stroke="#CA8A04" strokeWidth="2" />
              <circle cx="305" cy="299" r="8" fill="#DC2626" />

              {/* Top Hinged Guide Plate (Aluminium Precision Deck) */}
              <path
                d="M72 212L96 164H304L328 212H72Z"
                fill="#CBD5E1"
                stroke="#334155"
                strokeWidth="3"
              />
              <rect
                x="72"
                y="210"
                width="256"
                height="14"
                rx="3"
                fill="#94A3B8"
                stroke="#334155"
                strokeWidth="2"
              />

              {/* 9 Stainless Steel Abrasion Stations & Loading Weights */}
              {[
                { cx: 112, cy: 192 },
                { cx: 156, cy: 192 },
                { cx: 200, cy: 192 },
                { cx: 244, cy: 192 },
                { cx: 288, cy: 192 },
                { cx: 134, cy: 168 },
                { cx: 178, cy: 168 },
                { cx: 222, cy: 168 },
                { cx: 266, cy: 168 },
              ].map((st, idx) => (
                <g key={idx}>
                  {/* Station Base Ring */}
                  <ellipse
                    cx={st.cx}
                    cy={st.cy}
                    rx="15"
                    ry="7"
                    fill="#334155"
                    stroke="#0F172A"
                    strokeWidth="1.5"
                  />
                  {/* Stainless Steel 9kPa/12kPa Weight Cylinder */}
                  <rect
                    x={st.cx - 11}
                    y={st.cy - 28}
                    width="22"
                    height="26"
                    rx="3"
                    fill="#E2E8F0"
                    stroke="#475569"
                    strokeWidth="1.8"
                  />
                  {/* Spindle Rod */}
                  <rect
                    x={st.cx - 3}
                    y={st.cy - 48}
                    width="6"
                    height="22"
                    rx="2"
                    fill="#94A3B8"
                    stroke="#334155"
                    strokeWidth="1.2"
                  />
                  <ellipse
                    cx={st.cx}
                    cy={st.cy - 48}
                    rx="7"
                    ry="3"
                    fill="#0EA5E9"
                  />
                </g>
              ))}

              {/* Reference Badge if BIS Reference */}
              {variant === 'bis-reference' && (
                <g>
                  <rect x="125" y="54" width="150" height="24" rx="4" fill="#0F172A" />
                  <text
                    x="200"
                    y="70"
                    textAnchor="middle"
                    fill="#F8FAFC"
                    fontSize="9"
                    fontFamily="monospace"
                  >
                    CHUẨN MẪU BIS 1254×1254
                  </text>
                </g>
              )}
            </g>
          )}

          {sku === 'SDL-M238BB' && (
            <g>
              {/* SDL Atlas Electronic Crockmeter Chassis */}
              <rect
                x="70"
                y="230"
                width="260"
                height="98"
                rx="8"
                fill="#F8FAFC"
                stroke="#334155"
                strokeWidth="3"
              />
              {/* Red SDL Atlas Accent Bar */}
              <rect x="70" y="230" width="260" height="16" rx="4" fill="#DC2626" />
              {/* Specimen Testing Bed */}
              <rect
                x="86"
                y="196"
                width="140"
                height="34"
                rx="3"
                fill="#334155"
                stroke="#0F172A"
                strokeWidth="2"
              />
              {/* Reciprocating Chrome Rubbing Arm */}
              <rect
                x="110"
                y="150"
                width="150"
                height="12"
                rx="6"
                fill="#CBD5E1"
                stroke="#475569"
                strokeWidth="2"
              />
              {/* 9N Calibration Weight & 16mm Rubbing Finger */}
              <rect
                x="122"
                y="130"
                width="36"
                height="34"
                rx="4"
                fill="#94A3B8"
                stroke="#1E293B"
                strokeWidth="2"
              />
              <rect x="134" y="164" width="12" height="32" fill="#E2E8F0" stroke="#334155" strokeWidth="1.5" />
              {/* Digital LED Counter Panel */}
              <rect
                x="236"
                y="258"
                width="76"
                height="52"
                rx="4"
                fill="#0F172A"
                stroke="#475569"
                strokeWidth="2"
              />
              <text x="248" y="280" fill="#EF4444" fontSize="13" fontFamily="monospace" fontWeight="bold">
                0010
              </text>
              <text x="248" y="298" fill="#94A3B8" fontSize="8" fontFamily="monospace">
                SDL ATLAS M238BB
              </text>
            </g>
          )}

          {sku === 'XR-CI7800' && (
            <g>
              {/* X-Rite Ci7800 Benchtop Sphere Spectrophotometer */}
              <path
                d="M95 326L115 120C117 104 130 92 146 92H254C270 92 283 104 285 120L305 326H95Z"
                fill="#F1F5F9"
                stroke="#334155"
                strokeWidth="3"
              />
              {/* Optical Integrating Sphere Housing */}
              <circle
                cx="200"
                cy="185"
                r="52"
                fill="#1E293B"
                stroke="#475569"
                strokeWidth="4"
              />
              <circle
                cx="200"
                cy="185"
                r="22"
                fill="#090D16"
                stroke="#0EA5E9"
                strokeWidth="2.5"
              />
              {/* Sample Clamp Arm */}
              <rect
                x="148"
                y="248"
                width="104"
                height="16"
                rx="4"
                fill="#334155"
              />
              <text
                x="200"
                y="302"
                textAnchor="middle"
                fill="#0F172A"
                fontSize="12"
                fontFamily="monospace"
                fontWeight="bold"
              >
                X-Rite Ci7800
              </text>
              <text
                x="200"
                y="316"
                textAnchor="middle"
                fill="#64748B"
                fontSize="8"
                fontFamily="monospace"
              >
                0.08 ΔE*ab SPHERE
              </text>
            </g>
          )}

          {sku === 'BR-LAB70' && (
            <g>
              {/* Branca Idealair LAB-70 Vertical Conditioning Tower */}
              <rect
                x="122"
                y="72"
                width="156"
                height="264"
                rx="8"
                fill="#E2E8F0"
                stroke="#334155"
                strokeWidth="3"
              />
              {/* Upper Air Louver Grille */}
              <rect
                x="138"
                y="90"
                width="124"
                height="56"
                rx="4"
                fill="#1E293B"
              />
              {[102, 114, 126, 138].map((yPos) => (
                <line
                  key={yPos}
                  x1="146"
                  y1={yPos}
                  x2="254"
                  y2={yPos}
                  stroke="#94A3B8"
                  strokeWidth="2"
                />
              ))}
              {/* PLC Climate Touchscreen */}
              <rect
                x="152"
                y="168"
                width="96"
                height="58"
                rx="4"
                fill="#090D16"
                stroke="#0EA5E9"
                strokeWidth="2"
              />
              <text x="164" y="190" fill="#10B981" fontSize="10" fontFamily="monospace" fontWeight="bold">
                20.0°C ± 0.5
              </text>
              <text x="164" y="208" fill="#38BDF8" fontSize="10" fontFamily="monospace" fontWeight="bold">
                65.0% RH ISO139
              </text>
              <text
                x="200"
                y="265"
                textAnchor="middle"
                fill="#0F172A"
                fontSize="11"
                fontFamily="monospace"
                fontWeight="bold"
              >
                BRANCA IDEALAIR
              </text>
              <text
                x="200"
                y="282"
                textAnchor="middle"
                fill="#DC2626"
                fontSize="9"
                fontFamily="monospace"
              >
                LAB-70 · ITALY
              </text>
            </g>
          )}
        </svg>
      </div>
    </div>
  );
};
