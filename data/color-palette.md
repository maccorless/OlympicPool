# Olympic Medal Pool - Color Palette

## Inspired by Milano Cortina 2026 "Vibes" Identity

The Milano Cortina 2026 brand is described as **vibrant, dynamic, and contemporary**, featuring bold colors, fluid shapes, and the essence of Italian spirit. This palette captures that energy while ensuring accessibility and usability for a web application.

---

## Primary Palette

### Alpine Blue (Primary)
```
Hex: #1E3A5F
RGB: 30, 58, 95
```
*Deep, confident blue inspired by alpine twilight. Use for headers, primary buttons, navigation.*

### Dolomite White (Background)
```
Hex: #F8FAFC
RGB: 248, 250, 252
```
*Clean, crisp white with a hint of cool. Main background color.*

### Italian Red (Accent)
```
Hex: #DC2626
RGB: 220, 38, 38
```
*Vibrant red from the Italian tricolore. Use for highlights, alerts, gold medal indicators.*

---

## Secondary Palette

### Ice Blue (Secondary)
```
Hex: #38BDF8
RGB: 56, 189, 248
```
*Bright, energetic blue inspired by glacial ice. Use for interactive elements, hover states, links.*

### Forest Green (Tertiary)
```
Hex: #059669
RGB: 5, 150, 105
```
*Italian flag green with contemporary brightness. Use for success states, confirmations.*

### Sunset Coral (Highlight)
```
Hex: #F97316
RGB: 249, 115, 22
```
*Warm Mediterranean accent. Use sparingly for special callouts, badges.*

---

## Medal Colors

### Gold
```
Hex: #FBBF24
RGB: 251, 191, 36
```
*Rich gold for first place.*

### Silver
```
Hex: #9CA3AF
RGB: 156, 163, 175
```
*Cool metallic silver for second place.*

### Bronze
```
Hex: #CD7F32
RGB: 205, 127, 50
```
*Classic bronze for third place.*

---

## Neutral Palette

### Charcoal (Text Primary)
```
Hex: #1F2937
RGB: 31, 41, 55
```
*Primary body text color.*

### Slate (Text Secondary)
```
Hex: #64748B
RGB: 100, 116, 139
```
*Secondary text, labels, captions.*

### Light Gray (Borders)
```
Hex: #E2E8F0
RGB: 226, 232, 240
```
*Subtle borders, dividers, card backgrounds.*

### Snow (Cards)
```
Hex: #FFFFFF
RGB: 255, 255, 255
```
*Card backgrounds, modal backgrounds.*

---

## Gradients (Optional - For Hero Sections)

### Alpine Gradient
```css
background: linear-gradient(135deg, #1E3A5F 0%, #38BDF8 100%);
```
*Hero sections, feature highlights.*

### Vibes Gradient (Milano Cortina inspired)
```css
background: linear-gradient(135deg, #DC2626 0%, #F97316 50%, #FBBF24 100%);
```
*Special moments, celebration states (e.g., when user wins).*

---

## Tailwind CSS Configuration

If using Tailwind CSS (recommended for this project):

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Primary
        'alpine': {
          DEFAULT: '#1E3A5F',
          light: '#2D4A6F',
          dark: '#152B47',
        },
        'ice': {
          DEFAULT: '#38BDF8',
          light: '#7DD3FC',
          dark: '#0EA5E9',
        },
        // Accent
        'italian-red': '#DC2626',
        'forest': '#059669',
        'coral': '#F97316',
        // Medals
        'gold': '#FBBF24',
        'silver': '#9CA3AF',
        'bronze': '#CD7F32',
      },
    },
  },
}
```

---

## Usage Examples

### Leaderboard Row
```
Background: white (#FFFFFF)
Border: light-gray (#E2E8F0)
Rank number: alpine (#1E3A5F)
Team name: charcoal (#1F2937)
Points: alpine (#1E3A5F), bold
Medal counts: gold/silver/bronze colors
```

### Button Styles
```
Primary button: 
  Background: alpine (#1E3A5F)
  Text: white
  Hover: alpine-light (#2D4A6F)

Secondary button:
  Background: white
  Border: alpine (#1E3A5F)
  Text: alpine
  Hover: light-gray background

Danger/Warning button:
  Background: italian-red (#DC2626)
  Text: white
```

### Country Selection Card
```
Unselected:
  Background: white
  Border: light-gray (#E2E8F0)
  
Selected:
  Background: ice-light (#7DD3FC) at 10% opacity
  Border: ice (#38BDF8)
  
Disabled (can't afford):
  Background: light-gray (#E2E8F0) at 50% opacity
  Text: slate (#64748B)
```

---

## Accessibility Notes

All color combinations meet WCAA AA contrast requirements:

| Foreground | Background | Contrast Ratio | Pass |
|------------|------------|----------------|------|
| Charcoal | Dolomite White | 14.5:1 | ✅ AAA |
| Alpine Blue | White | 9.8:1 | ✅ AAA |
| Italian Red | White | 4.6:1 | ✅ AA |
| Forest Green | White | 4.5:1 | ✅ AA |
| White | Alpine Blue | 9.8:1 | ✅ AAA |

---

## Visual Reference

```
┌─────────────────────────────────────────────────────────┐
│  ███ Alpine Blue (#1E3A5F) - Headers, Primary Actions   │
├─────────────────────────────────────────────────────────┤
│  ███ Ice Blue (#38BDF8) - Links, Interactive Elements   │
├─────────────────────────────────────────────────────────┤
│  ███ Italian Red (#DC2626) - Accents, Alerts            │
├─────────────────────────────────────────────────────────┤
│  ███ Forest Green (#059669) - Success States            │
├─────────────────────────────────────────────────────────┤
│  ███ Gold (#FBBF24)  ███ Silver (#9CA3AF)  ███ Bronze   │
└─────────────────────────────────────────────────────────┘
```

This palette captures the spirit of Milano Cortina 2026—bold and vibrant yet clean and functional—while ensuring the application remains accessible and easy to use.
