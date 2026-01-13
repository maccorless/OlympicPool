# Product Requirements Document: Olympic Medal Pool

## 1. Executive Summary

### 1.1 Product Overview
The Olympic Medal Pool is a fantasy-sports-style web application where participants "draft" countries by spending a budget, then earn points based on those countries' actual medal performance at the Olympic Games.

### 1.2 Business Objective
Create a fun, engaging team activity for DTEC colleagues during the Olympic Games, starting with Milano Cortina 2026 Winter Olympics.

### 1.3 Key Value Proposition
- Simple, intuitive drafting experience
- Real-time (or near-real-time) leaderboard updates via automated ODF integration
- Mobile-friendly leaderboard for on-the-go checking during Games

---

## 2. Target Users

### 2.1 Primary Users: Contest Participants
- **Who**: DTEC team members and invited colleagues
- **Knowledge level**: Varies from casual Olympics viewers to highly knowledgeable
- **Expected volume**: ~200 total users, with materially lower concurrent usage
- **Primary devices**: Mobile for leaderboard viewing; desktop/mobile for draft creation

### 2.2 Secondary Users: Administrator
- **Who**: Single admin (Ken)
- **Responsibilities**: Contest setup, country import, troubleshooting, manual corrections if needed

---

## 3. Contest Rules & Mechanics

### 3.1 Draft Rules
| Parameter | Value |
|-----------|-------|
| Budget per participant | 200 points |
| Maximum countries per entry | 10 |
| Entries per participant | 1 |
| Entry deadline | Start of competition (Feb 4, 2026 for MiCo26) |
| Changes allowed | Yes, until entry deadline |
| Pick visibility | Private until deadline; public after |

### 3.2 Scoring System
| Medal | Points |
|-------|--------|
| Gold | 3 |
| Silver | 2 |
| Bronze | 1 |

### 3.3 Tiebreaker Rules (in order)
1. Total points (gold×3 + silver×2 + bronze×1)
2. Total gold medals
3. Total silver medals
4. Total bronze medals

**If still tied after all tiebreakers, teams share the same rank.** (e.g., two teams at #3, next team is #5)

### 3.4 Country Costs
Each country has a cost (1-200 points) roughly tied to projected medal performance. Costs are set by admin via spreadsheet import before the contest opens.

---

## 4. Functional Requirements

### 4.1 User Authentication

#### 4.1.1 Registration
- **Required fields**: Name, Team Name, Email
- **Validation**: Email must be unique in system
- **Duplicate email handling**: Display message "An account with this email already exists. A login link has been sent to your email."

#### 4.1.2 Authentication Flow
- **Method**: Passwordless magic link via email
- **Session duration**: 21 days
- **Session scope**: Device-specific (new device requires new login)
- **Email service**: Resend

#### 4.1.3 Magic Link Email Content
```
Subject: Your Olympic Medal Pool Login Link

Hi {name},

Click here to access the Olympic Medal Pool:
{login_link}

This link expires in 1 hour.

If you didn't request this, you can ignore this email.
```

### 4.2 Draft Picker (User)

#### 4.2.1 Display Requirements
- Country name
- Country flag (emoji or image)
- Country cost
- Running totals: remaining budget, countries selected count
- Selected countries list with ability to deselect

#### 4.2.2 Constraints (Client-Side Validation)
- Cannot exceed 200 point budget
- Cannot exceed 10 countries
- Cannot select same country twice

#### 4.2.3 Submission
- "Submit Picks" button disabled until at least 1 country selected
- On submit: Display confirmation with summary
- Email confirmation sent to user

#### 4.2.4 Confirmation Email Content
```
Subject: Your Olympic Medal Pool Entry Confirmed

Hi {name},

Your entry "{team_name}" has been saved!

Your picks:
{list of countries with costs}

Total spent: {x}/200 points
Countries selected: {y}/10

You can update your picks until {deadline}.

Good luck!
```

#### 4.2.5 Edit Mode
- User can return and modify picks until deadline
- Previous selections pre-populated
- Same constraints apply

### 4.3 Leaderboard (Public after deadline)

#### 4.3.1 Display Columns
- Rank
- Team Name
- Total Points
- Gold count
- Silver count
- Bronze count
- Total medals

#### 4.3.2 Sorting Options
- Total points (default, descending)
- Team name (alphabetical)
- Gold medals (descending)
- Silver medals (descending)
- Bronze medals (descending)
- Total medals (descending)

#### 4.3.3 Drill-Down
Clicking a team name shows:
- Participant name
- List of selected countries with their:
  - Flag
  - Name
  - Cost paid
  - Current medal counts (G/S/B)
  - Current points earned

### 4.4 Admin Functions

#### 4.4.1 Contest Setup
- Set contest name (e.g., "Milano Cortina 2026")
- Set entry deadline (date/time picker)
- Set budget limit (default: 200)
- Set max countries (default: 10)

#### 4.4.2 Country Import
**Method**: Copy-paste from spreadsheet into HTML table interface

**Required columns**:
| Column | Description |
|--------|-------------|
| Country Code | 3-letter IOC code (e.g., USA, ITA, NOR) |
| Country Name | Full name |
| Projected Medals | Reference number (not used in scoring) |
| Cost | Point cost to draft (1-200) |

**Interface behavior**:
- Paste data into textarea or editable table
- Preview parsed data before import
- Validate: no duplicate codes, all costs are valid numbers
- Confirm to save

#### 4.4.3 Country Management (Post-Import)
- View all countries with costs
- Edit individual country cost
- Add single country manually
- Remove country (only if no participants have selected it)

#### 4.4.4 Participant Management
- View all registered participants
- View participant's picks
- Manual correction capability (for technical issues only):
  - Edit participant's picks after deadline
  - Add/remove countries from entry
  - Log correction reason

#### 4.4.5 Medal Ingestion

**MVP**: Manual medal entry interface:
- Select country
- Enter medal counts (G/S/B)
- Save with timestamp

**Phase 2**: Sports Data Hub API Integration

**Source**: Sports Data Hub medals table API

**Approach**: Lazy refresh triggered by user activity
1. On any user action (login, view leaderboard, etc.), check `medals_last_updated` timestamp
2. If timestamp is within `MEDAL_REFRESH_MINUTES` (configurable, default 15), do nothing
3. If stale, fire **asynchronous** API call to Sports Data Hub
4. Parse full medals table response and update local `medals` table
5. Update `medals_last_updated` timestamp
6. User sees current cached data immediately; fresh data appears on next page load

**Why async**: API call should not block user request. User gets fast response with slightly stale data; refresh happens in background.

**Configuration**:
```
MEDAL_REFRESH_MINUTES=15      # How often to refresh
SPORTS_DATA_HUB_URL=          # API endpoint
SPORTS_DATA_HUB_API_KEY=      # If required
```

#### 4.4.6 Contest State Management
| State | Description |
|-------|-------------|
| Setup | Admin configuring, not visible to users |
| Open | Users can register and submit picks |
| Locked | Deadline passed, picks frozen, medals being awarded |
| Complete | All medals awarded, final standings |

**State Enforcement Rules:**

| Action | Setup | Open | Locked | Complete |
|--------|-------|------|--------|----------|
| View home page | ✓ "Coming soon" | ✓ | ✓ | ✓ |
| Register/Login | ✗ | ✓ | ✓ | ✓ |
| View/edit draft | ✗ | ✓ | ✗ (view only) | ✗ (view only) |
| Submit picks | ✗ | ✓ | ✗ | ✗ |
| View leaderboard | ✗ | ✗ | ✓ | ✓ |
| Admin: edit config | ✓ | ✓ | ✓ | ✗ |
| Admin: enter medals | ✗ | ✗ | ✓ | ✓ |

**State transitions:** `setup` → `open` → `locked` → `complete` (forward only, no rollback)

---

## 5. Non-Functional Requirements

### 5.1 Local Development
The application must run completely locally on a MacBook Pro with no external dependencies except email (which can be mocked):

| Component | Local | Production |
|-----------|-------|------------|
| Database | SQLite file | SQLite file |
| Web server | Flask dev server | Gunicorn |
| Email | Console output / mock | Resend API |
| Medal data | Manual entry | Manual / Sports Data Hub |

**Local setup should be:**
```bash
# Clone and setup
git clone <repo>
cd olympic-medal-pool
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
flask init-db

# Run locally
flask run
```

No Docker, no external databases, no complex setup. A developer should be able to clone and run in under 5 minutes.

### 5.2 Performance
- Page load: < 2 seconds
- Leaderboard update: Acceptable latency of 15 minutes
- Concurrent users: Support 50 simultaneous users

### 5.3 Availability
- Target: 99% uptime during Games period
- Acceptable maintenance windows: Outside medal event hours

### 5.4 Mobile Responsiveness
| Feature | Mobile Priority |
|---------|----------------|
| Leaderboard | Critical - must work perfectly |
| Draft picker | Important - should work well |
| Admin interface | Not required - desktop only acceptable |

### 5.5 Browser Support
- Chrome (latest 2 versions)
- Safari (latest 2 versions)
- Firefox (latest 2 versions)
- Mobile Safari (iOS 15+)
- Chrome Mobile (Android 10+)

---

## 6. Technical Specification

### 6.1 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Browser/Mobile │────▶│  Flask Server   │────▶│    SQLite DB    │
│  (HTMX + Alpine)│     │                 │     │                 │
│                 │◀────│                 │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │     Resend      │
                        │  (Email API)    │
                        └─────────────────┘
```

### 6.2 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend | Flask (Python) | Simple, familiar, minimal boilerplate |
| Frontend | HTMX + Alpine.js | Server-driven updates + lightweight client reactivity for draft picker |
| Database | SQLite | Zero config, handles 200 users easily, single-file backup |
| Hosting | Railway (paid) | Traditional server model, SQLite works, no cold starts |
| Email | Resend | Simple API, generous free tier |

### 6.3 Data Model

The authoritative schema is in `schema.sql`. See `CLAUDE.md` for the complete SQL.

**Tables overview:**

| Table | Purpose |
|-------|---------|
| `contest` | Single-row config: state, deadline, budget, max_countries |
| `users` | User accounts with email, name, team_name |
| `countries` | Reference data: IOC code, ISO code (for flags), name, expected_points, cost |
| `picks` | User selections: user_id + country_code |
| `medals` | Actual medal counts + calculated points per country |
| `tokens` | Magic links and session tokens |
| `system_meta` | Key-value store for refresh timestamps |

**Key design decisions:**
- `countries.iso_code` stores 2-letter ISO code for flag image URLs (e.g., `flagcdn.com/w40/no.png`)
- `medals.points` is pre-calculated (`gold*3 + silver*2 + bronze`) on every update for query efficiency
- Budget and max_countries constraints are enforced in application code for user-friendly error messages

### 6.4 API Endpoints

See `CLAUDE.md` for the detailed route contract including auth requirements and response types (page vs fragment).

#### Public Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | / | Home/landing page |
| GET | /register | Registration form |
| POST | /register | Submit registration |
| GET | /login | Request login link form |
| POST | /login | Send magic link |
| GET | /auth/{token} | Consume magic link, set session |
| GET | /logout | End session |
| GET | /leaderboard | View standings (locked/complete only) |
| GET | /team/{user_id} | View participant's picks |

#### Authenticated User Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | /draft | Draft picker interface |
| POST | /draft/toggle | HTMX: toggle country selection (returns fragment) |
| POST | /draft/submit | Submit final picks |
| GET | /my-picks | View own picks |

#### Admin Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | /admin | Admin dashboard |
| GET | /admin/contest | Contest config form |
| POST | /admin/contest | Save contest config |
| GET | /admin/countries | Country list + import form |
| POST | /admin/countries/import | Import countries from CSV |
| GET | /admin/medals | Medal entry interface |
| POST | /admin/medals | Update medal counts |
| GET | /admin/users | User list |

### 6.5 HTMX Patterns

#### Draft Picker Interactions
```html
<!-- Country selection with Alpine.js state -->
<div x-data="draftPicker()">
  <div class="budget-display">
    Budget: <span x-text="remainingBudget"></span>/200
    Countries: <span x-text="selectedCount"></span>/10
  </div>
  
  <div class="country-grid">
    <template x-for="country in countries">
      <button 
        @click="toggleCountry(country)"
        :class="{ 'selected': isSelected(country.id) }"
        :disabled="!canSelect(country) && !isSelected(country.id)"
      >
        <span x-text="country.flag"></span>
        <span x-text="country.name"></span>
        <span x-text="country.cost"></span>
      </button>
    </template>
  </div>
  
  <!-- Submit via HTMX -->
  <button 
    hx-post="/draft"
    hx-vals="js:{countries: getSelectedIds()}"
    :disabled="selectedCount === 0"
  >
    Submit Picks
  </button>
</div>
```

#### Leaderboard Sorting
```html
<table hx-get="/leaderboard" hx-trigger="load">
  <thead>
    <tr>
      <th>Rank</th>
      <th hx-get="/leaderboard?sort=team_name" hx-target="closest table">Team</th>
      <th hx-get="/leaderboard?sort=points" hx-target="closest table">Points</th>
      <!-- ... -->
    </tr>
  </thead>
  <tbody id="leaderboard-body">
    <!-- Populated by HTMX -->
  </tbody>
</table>
```

---

## 7. User Interface Design

### 7.1 Branding

**Color Palette** (inspired by Milano Cortina 2026 "Vibes" identity):

| Use | Color | Notes |
|-----|-------|-------|
| Primary | Deep Blue | Main actions, headers |
| Secondary | Vibrant Red/Coral | Accents, highlights |
| Tertiary | Fresh Green | Success states |
| Background | Clean White | Main background |
| Text | Dark Gray | Body text |
| Accent | Ice Blue/White gradients | Winter feel |

*Note: Sample exact hex values from milanocortina2026.org for final implementation*

**Typography**:
- Headers: Bold, modern sans-serif
- Body: Clean sans-serif (system fonts for performance)

**Design Principles** (per Milano Cortina brand):
- Vibrant and dynamic
- Contemporary and clean
- Italian spirit - expressive but elegant

### 7.2 Page Layouts

#### Landing Page
```
┌─────────────────────────────────────────┐
│  🏅 Olympic Medal Pool                  │
│  Milano Cortina 2026                    │
├─────────────────────────────────────────┤
│                                         │
│  Draft your countries.                  │
│  Win bragging rights.                   │
│                                         │
│  [Enter Contest]    [View Leaderboard]  │
│                                         │
│  ─────────────────────────────────────  │
│  How It Works:                          │
│  1. Spend 200 points on up to 10        │
│     countries                           │
│  2. Earn points when your countries     │
│     win medals                          │
│  3. Track your ranking on the           │
│     leaderboard                         │
│                                         │
│  Entry deadline: Feb 4, 2026            │
└─────────────────────────────────────────┘
```

#### Draft Picker (Mobile)
```
┌─────────────────────────────────────────┐
│  ← My Draft                             │
├─────────────────────────────────────────┤
│  Budget: 142/200  │  Teams: 4/10        │
├─────────────────────────────────────────┤
│  Your Picks:                            │
│  🇳🇴 Norway (58) ✕                       │
│  🇩🇪 Germany (42) ✕                      │
│  ... (scrollable)                       │
├─────────────────────────────────────────┤
│  🔍 Search countries...                 │
├─────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ 🇳🇴      │ │ 🇩🇪      │ │ 🇺🇸      │   │
│  │ Norway  │ │ Germany │ │ USA     │   │
│  │ 58 pts  │ │ 42 pts  │ │ 35 pts  │   │
│  │ [Added] │ │ [Added] │ │ [+ Add] │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│  (grid continues, scrollable)           │
├─────────────────────────────────────────┤
│  [        Submit Picks (4 teams)      ] │
└─────────────────────────────────────────┘
```

#### Leaderboard (Mobile)
```
┌─────────────────────────────────────────┐
│  🏆 Leaderboard           [Sort ▼]      │
├─────────────────────────────────────────┤
│  #1  Team Viking                        │
│      156 pts  │  🥇12 🥈8 🥉6            │
├─────────────────────────────────────────┤
│  #2  Alpine Dreams                      │
│      148 pts  │  🥇10 🥈9 🥉11           │
├─────────────────────────────────────────┤
│  #3  Frozen Picks                       │
│      142 pts  │  🥇9 🥈11 🥉8            │
├─────────────────────────────────────────┤
│  ... (scrollable)                       │
│                                         │
│  #47 My Team Name  ← You                │
│      89 pts   │  🥇5 🥈6 🥉7             │
└─────────────────────────────────────────┘
```

---

## 8. Security Considerations

### 8.1 Authentication
- Magic links expire after 1 hour
- Magic links are single-use
- Session tokens are cryptographically random (32 bytes)
- Sessions stored server-side, only token ID in cookie
- HttpOnly, Secure, SameSite=Lax cookies

### 8.2 Authorization
- Admin routes protected by admin flag check
- Users can only view/edit their own picks (before deadline)
- Picks become read-only after deadline (except admin corrections)

### 8.3 Data Validation
- All inputs sanitized server-side
- Country codes validated against known list
- Budget/count constraints enforced server-side (not just client)
- Rate limiting on magic link requests (max 3 per email per hour)

### 8.4 Admin Access
- Single admin account, identified by email in environment variable
- Admin uses same magic link authentication as regular users (21-day session)
- Admin flag set based on email match, not separate credentials
- Admin corrections logged with timestamp and reason

---

## 9. Future Enhancements (Out of Scope for MVP)

### 9.1 Multi-Games Support (Phase 2)
- Games entity to support multiple editions
- Historical results preservation
- User participation history across Games

### 9.2 Sports Data Hub Integration (Phase 2)
- API client for Sports Data Hub medals endpoint
- Lazy refresh pattern (on user activity, if data stale)
- Async background updates (non-blocking)
- Configurable refresh interval

### 9.3 Nice-to-Have Features
- Real-time leaderboard via WebSockets
- Push notifications for medal updates
- Social sharing of picks/results
- Achievement badges
- Mini-leagues (sub-groups within main contest)

---

## 10. Success Metrics

### 10.1 Engagement
- Target: 80%+ of invited users register
- Target: 90%+ of registered users submit picks

### 10.2 Usability
- Zero support requests related to draft submission
- Mobile leaderboard works smoothly on all tested devices

### 10.3 Reliability
- No data loss
- Leaderboard accurate within 15 minutes of medal results

---

## 11. Timeline & Milestones

| Milestone | Target Date | Description |
|-----------|-------------|-------------|
| PRD Complete | Jan 2025 | This document finalized |
| MVP Development | Jan-Feb 2025 | Core functionality built |
| Internal Testing | Early Feb 2025 | Ken + small group test |
| Launch | Feb 1, 2025 | Open for registration |
| Entry Deadline | Feb 4, 2026 | Picks locked |
| Games Period | Feb 6-22, 2026 | Active medal tracking |
| Post-Games | Feb 23, 2026 | Final standings, retrospective |

---

## 12. Appendix

### 12.1 Country Flag Emoji Reference
Use Unicode flag emoji (e.g., 🇺🇸 🇳🇴 🇩🇪) which are supported on all modern browsers and mobile devices.

### 12.2 IOC Country Codes
Standard 3-letter IOC codes will be used. Full list available at: https://en.wikipedia.org/wiki/List_of_IOC_country_codes

### 12.3 Sports Data Hub API Reference (Phase 2)
Endpoint: TBD (internal Olympics Sports Data Hub)

Expected response format (medals by country):
```json
{
  "updated_at": "2026-02-10T14:30:00Z",
  "medals": [
    {"country_code": "NOR", "gold": 5, "silver": 3, "bronze": 4},
    {"country_code": "GER", "gold": 4, "silver": 5, "bronze": 2},
    ...
  ]
}
```

Key fields:
- `updated_at` - Timestamp of data
- `country_code` - IOC 3-letter code
- `gold`, `silver`, `bronze` - Medal counts

### 12.4 Companion Documents
The following companion documents provide additional detail for implementation:

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | Technical guidance for Claude Code during development |
| `countries.sql` | Country data with costs for Milano Cortina 2026 (import into SQLite) |
| `color-palette.md` | Color palette inspired by Milano Cortina 2026 brand |
| `MiCo2026_Country_Pricing.xlsx` | Source spreadsheet for country pricing |

---

## 13. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 10, 2025 | Ken + Claude | Initial PRD |
| 1.1 | Jan 12, 2025 | Ken + Claude | Added local dev requirements, Sports Data Hub integration, multiple admins |
| 1.2 | Jan 12, 2025 | Ken + Claude | Added state machine enforcement rules, simplified schema to match CLAUDE.md, aligned routes |
| 1.3 | Jan 12, 2025 | Ken + Claude | Added iso_code for flag images, pre-calculated points field in medals table |
| 1.4 | Jan 12, 2025 | Ken + Claude | Fixed tiebreaker order (points first), allow ties, simplified auth to Flask sessions |
| 1.5 | Jan 12, 2025 | Ken + Claude | Added unhappy path flows and UX polish guidelines to CLAUDE.md |
