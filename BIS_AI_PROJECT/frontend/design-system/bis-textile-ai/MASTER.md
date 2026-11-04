# Design System Master File — BIS TEXTILE AI (UI/UX Pro Max)

> **LOGIC:** When building or updating a specific page/tab, first check `design-system/bis-textile-ai/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** BIS TEXTILE AI — Hệ thống Điều hành & Chuẩn hóa Sản phẩm Dệt May
**CLI Initialized:** `npx uipro-cli init --ai gemini --offline --force` & `npx uipro-cli init --ai antigravity --offline --force`
**Skill Paths:** `.gemini/skills/ui-ux-pro-max/` · `.agent/skills/ui-ux-pro-max/`
**Category:** B2B Industrial AI Multi-Agent Command Center & E-Commerce Product Standardization Studio

---

## Global Rules

### Color Palette (8D Metallic Bronze-Obsidian & Warm Ivory Inspection)

| Role | Hex | CSS Variable / Class | Usage |
|------|-----|----------------------|-------|
| Canvas Obsidian | `#161210` | `.agent-floor-grid` | Physical brushed-metallic 3D workspace floor surface |
| Dark Espresso Shell | `#231C18` | `.card-8d-dark` | Command center headers, dark shells, 3D stage frame |
| Primary Ivory Surface | `#F6F1EA` | `.card-8d-ivory` | High-contrast 4.5:1+ inspection cards (Technical, Marketing, Image Studio, Operations, Knowledge, Memory) |
| Interactive Porcelain | `#FFFDF9` | `.card-8d-interactive` | Clickable meeting cards, candidate image tiles, spec items |
| Primary Brand CTA | `#D9382C` | `.btn-8d-crimson` | Primary action buttons ("Tạo bản nháp", "Lưu thông số", "Phê duyệt ảnh") |
| Champagne Bronze | `#F59E0B` | `--agent-technical` | Metallic floor joints, active step highlights, Technical Agent |
| Text Primary (Light Card) | `#231C18` | `text-[#231C18]` | Primary body & heading text on warm ivory cards (Contrast > 11:1) |
| Text Muted (Light Card) | `#5C4D43` | `text-[#5C4D43]` | Secondary metadata on warm ivory cards (Contrast > 5.4:1) |

### Typography

- **Heading & UI Font:** `Plus Jakarta Sans`, `-apple-system`, `BlinkMacSystemFont`, `sans-serif`
- **Technical / SKU / Citation Font:** `JetBrains Mono`, `ui-monospace`, `SFMono-Regular`, `monospace` (`tabular-nums`)
- **Mood:** Industrial precision, tactile 8D depth, bilingual VI/EN clarity, laboratory-grade readability

### 8D Tactile Depth & Metallic Floor Surface

- **`.agent-floor-grid`**: Dual-scale `48px × 48px` primary structural floor plates (`rgba(253, 230, 138, 0.085)` champagne-bronze bevel + `rgba(12, 8, 6, 0.55)` recessed seam shadow) with `16px × 16px` micro-machined sub-grid (`rgba(255, 245, 232, 0.028)`).
- **`.card-8d-dark` / `.card-8d-ivory` / `.card-8d-interactive`**: Soft multi-layered drop shadows combined with top specular rim highlights (`inset 0 1px 0`) and subtle directional surface gradients.

---

## Pre-Delivery Checklist (UI/UX Pro Max Verified)

- [x] No emojis used as UI icons (100% Lucide SVG icons across navigation, pipeline, and workspaces)
- [x] `cursor-pointer` enforced on all clickable buttons, tabs, cards, and 3D HUD controls
- [x] Hover states use smooth transitions (`150ms–200ms`) with subtle elevation (`translateY(-1.5px)`) without layout shift
- [x] Light/Ivory inspection cards maintain > 4.5:1 text contrast (`#231C18` and `#5C4D43` on `#F6F1EA`)
- [x] Visible `:focus-visible` keyboard focus rings across interactive elements
- [x] `prefers-reduced-motion` respected both via OS media query and in-app "Giảm chuyển động" toggle
- [x] Responsive across mobile, tablet, and desktop viewports (`375px`, `768px`, `1024px`, `1440px`)
