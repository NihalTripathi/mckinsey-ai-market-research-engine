# McKinsey AI Market Research & Strategy Engine — Frontend Module

> **Academic Capstone Project &bull; AlmaBetter**  
> *Independent educational prototype — Not an official McKinsey & Company product.*

---

## 1. Project Overview

The **McKinsey AI Market Research & Strategy Engine** is an academic platform designed to automate management consulting market research and strategic intelligence briefs.

This module represents the **Research Query Page (Intake Interface)**. It provides a consulting-grade, high-trust frontend where business consultants or executive users configure five critical parameters to initiate an end-to-end market analysis across **12 strategic frameworks**.

---

## 2. Technology Stack

- **Runtime:** Node.js (v18+)
- **Backend Server:** Express.js (v5 / v4 compatible)
- **Frontend Core:** Pure HTML5, Modern CSS3, and Vanilla JavaScript (ES6+)
- **Styling & Fonts:** Custom CSS matching McKinsey design system typography (`Inter` & `Newsreader`), responsive flexbox/grid layout
- **Assets:** Optimized local corporate building photograph, inline scalable vector icons (SVG)
- **Zero Heavy Frameworks:** No React, Next.js, or external UI libraries required to run, ensuring maximum transparency, fast load times, and ease of academic evaluation.

---

## 3. Project Folder Structure

```text
mckinsey-market-research/
├── public/
│   ├── index.html            # Main redesigned research query interface
│   ├── css/
│   │   └── style.css         # Complete responsive styles & design tokens
│   ├── js/
│   │   └── app.js           # Client-side validation, fetch API & UI states
│   └── images/
│       └── corporate-building.jpg  # Local corporate building photograph
├── server.js                 # Express server & /api/research endpoint
├── package.json              # Express dependencies and launch scripts
├── package-lock.json         # Locked dependency versions
├── README.md                 # Project guide & handover documentation
└── API_INTEGRATION.md        # Technical contract for LangGraph / AI integration
```

---

## 4. Installation & Local Setup

### Prerequisites
- Node.js installed (v18.0.0 or higher recommended)
- npm (Node Package Manager)

### Step 1: Install Dependencies
Open a terminal in the project directory and run:
```bash
npm install
```

### Step 2: Start the Local Server
```bash
npm start
# or
node server.js
```

### Step 3: Open in Browser
Visit: **[http://localhost:3000](http://localhost:3000)**

---

## 5. Completed Frontend Features

1. **Header & Navigation**:
   - McKinsey branding with `Strategy Engine` title and `Academic Project` pill badge.
   - Interactive navigation tabs: `Research` (active indicator), `Sample Report` (modal preview), `Methodology` (modal preview).
2. **Hero Section**:
   - High-contrast title: `AI Market Research` with custom blue accent indicator.
   - Strategic subtitle explaining automated intelligence briefing.
   - Sourced local corporate high-rise glass building photograph.
3. **Research Configuration (Left Panel)**:
   - **1. Research Question** (*Required*): Multiline textarea with user icon and `Core problem or objective` guide.
   - **2. Target Market** (*Required*): Text input with analytics icon for sector/industry specification.
   - **3. Geography** (*Required*): Dropdown (`India`, `United States`, `Global`, `Other`). Dynamically displays custom text input when `Other` is selected.
   - **4. Timeframe** (*Optional*): Dropdown with `Optional` badge, defaults to `Last 3 Years (Default)`.
   - **5. Competitors** (*Optional*): Text input with `Optional` badge for peer companies.
   - **Primary Action Button**: Full-width navy blue `Generate Research Plan →` with real-time loading spinner and disabled state prevention.
4. **How It Works (Right Top Panel)**:
   - 3-step sequential workflow visualization: `Provide Input` &rarr; `Run Analysis` &rarr; `Get Research Plan`.
5. **Research Output Scope (Right Bottom Panel)**:
   - 2-column checklist displaying all **12 analyses** targeted by the engine (Market Sizing, TAM, SWOT, Porter's 5 Forces, Customer Personas, etc.).
6. **Form Validation & Real-time Feedback**:
   - Client-side error messages appear below invalid fields with red border highlights.
   - Errors clear automatically as the user types.
7. **Local Request Dispatch & Confirmation**:
   - Submits payload via asynchronous `fetch` to `/api/research`.
   - Displays clear success banner: *"Research request saved locally. Backend integration pending."* with Plan ID and parameter summary grid.

---

## 6. Pending Backend Integration (For Next Team Member)

This frontend module is verified and ready for handoff. The backend API (`server.js`) currently receives, validates, and stores queries locally with the flag:
```json
"agentStatus": "READY_FOR_LANGGRAPH_INTEGRATION"
```

Please refer to **`API_INTEGRATION.md`** for full instructions on connecting your LangGraph research workflow and AI multi-agent orchestration.
