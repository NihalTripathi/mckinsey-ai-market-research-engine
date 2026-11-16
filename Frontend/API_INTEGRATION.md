# API Integration Contract & Handover Guide

> **Target:** Next Team Member / LangGraph AI Research Engineer  
> **Module:** Research Query Intake &rarr; AI Planner Agent Orchestration

---

## 1. Overview

This document specifies the exact JSON contract, data types, validation constraints, and integration hooks for connecting the frontend interface to the **LangGraph multi-agent research workflow**.

---

## 2. Form Input Fields Specification

| Field Name | HTML / JSON Key | Type | Requirement | Default Value | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Research Question** | `researchQuestion` | String | **Required** | `""` | Multiline question or hypothesis (min 5 chars). |
| **Target Market** | `targetMarket` | String | **Required** | `""` | Industry or niche (e.g., "EV", "FinTech"). |
| **Geography** | `geography` | String | **Required** | `""` | Options: `India`, `United States`, `Global`, `Other`. |
| **Custom Geography** | `customGeography` | String | Conditional | `""` | Required only when `geography === "Other"`. |
| **Timeframe** | `timeframe` | String | Optional | `"Last 3 Years (Default)"` | Options: `Last 1 Year`, `Last 3 Years (Default)`, `Last 5 Years`. |
| **Competitors** | `competitors` | String | Optional | `""` | Comma-separated competitor names. |

---

## 3. Frontend-to-Backend HTTP Request Contract

- **Endpoint:** `POST /api/research`
- **Content-Type:** `application/json`

### Example Request Body (JSON)
```json
{
  "researchQuestion": "How can electric commercial vehicle fleets scale profitable unit economics across Tier-2 logistics in India?",
  "targetMarket": "Electric Commercial Vehicles & Logistics",
  "geography": "India",
  "customGeography": "",
  "timeframe": "Last 3 Years (Default)",
  "competitors": "Tata Motors, Mahindra Electric, Switch Mobility"
}
```

---

## 4. Server-Side Processing & Default Injections

In `server.js`, the request is validated and enriched with the **McKinsey Strategy Engine Configurable Defaults**:

```javascript
const backendDefaults = {
  deliverableFormat: "Strategy Brief",
  reportDepth: "Standard (12 Analyses)",
  sourcePreference: "Public & Verified Secondary Sources",
  reportPurpose: "Internal Strategic Review"
};
```

---

## 5. Expected API Response Contracts

### A. Success Response (HTTP 200 OK)
```json
{
  "success": true,
  "message": "Research request saved locally. Backend integration pending.",
  "data": {
    "id": "PLAN-1793886077678",
    "createdAt": "2026-11-05T13:41:17.678Z",
    "inputs": {
      "researchQuestion": "How can electric commercial vehicle fleets scale profitable unit economics across Tier-2 logistics in India?",
      "targetMarket": "Electric Commercial Vehicles & Logistics",
      "geography": "India",
      "timeframe": "Last 3 Years (Default)",
      "competitors": "Tata Motors, Mahindra Electric, Switch Mobility"
    },
    "systemDefaults": {
      "deliverableFormat": "Strategy Brief",
      "reportDepth": "Standard (12 Analyses)",
      "sourcePreference": "Public & Verified Secondary Sources",
      "reportPurpose": "Internal Strategic Review"
    },
    "plannedAnalyses": [
      "Market Sizing & TAM",
      "Competitive Landscape",
      "Customer Personas",
      "Industry Trends (5-Year)",
      "SWOT + Porter's Five Forces",
      "Pricing Strategy (3-Tier)",
      "Go-to-Market Plan",
      "Customer Journey Mapping",
      "Financial Modeling (3-Year)",
      "Risk Assessment (15 Risks)",
      "Market Entry Strategy (12-Month)",
      "Executive Strategy Synthesis"
    ],
    "agentStatus": "READY_FOR_LANGGRAPH_INTEGRATION",
    "workflowPending": true
  }
}
```

### B. Validation Failure Response (HTTP 400 Bad Request)
```json
{
  "success": false,
  "message": "Server-side validation failed.",
  "errors": {
    "researchQuestion": "Research question is required.",
    "targetMarket": "Target market is required."
  }
}
```

### C. Server Error Response (HTTP 500 Internal Server Error)
```json
{
  "success": false,
  "message": "Internal server error processing research request.",
  "error": "Database/Agent initialization timeout."
}
```

---

## 6. Where the Next Team Member Should Connect the LangGraph Workflow

Open `server.js` and locate lines 80–115:

```javascript
/*
 * =========================================================================
 * NOTE FOR NEXT TEAM MEMBER (LANGGRAPH / PLANNER AGENT INTEGRATION):
 * =========================================================================
 * In the next development phase, connect your LangGraph workflow here:
 * 
 * const { runResearchWorkflow } = require('./agents/langgraph_orchestrator');
 * const workflowResult = await runResearchWorkflow(researchPlanPayload);
 * 
 * return res.status(200).json({
 *   success: true,
 *   message: "Research strategy plan synthesized successfully.",
 *   data: workflowResult
 * });
 * =========================================================================
 */
```

### Recommended LangGraph Multi-Agent Architecture
The incoming `researchPlanPayload` should be dispatched to your LangGraph StateGraph:

```text
[Input Query Payload]
        │
        ▼
 ┌───────────────┐
 │ Planner Agent │  (Decomposes question into 3 parallel sub-graphs)
 └───────┬───────┘
         ├───────────────────────┼────────────────────────┐
         ▼                       ▼                        ▼
┌──────────────────┐   ┌────────────────────┐   ┌─────────────────────┐
│  Market Analyst  │   │ Competitor Analyst │   │ Strategic Synthesis │
│ (TAM, CAGR, GTM) │   │ (SWOT, Benchmarks) │   │ (15 Risks, Brief)   │
└────────┬─────────┘   └─────────┬──────────┘   └──────────┬──────────┘
         └───────────────────────┼────────────────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │ Executive Brief Output│ (12 Analyses Completed)
                     └───────────────────────┘
```

---

## 7. Frontend State Handling Summary

- **Client Validation:** Handled in `public/js/app.js` (`validateForm()`).
- **Loading State:** The submit button disables, changes color, and displays an animated spinner with `"Structuring Research Plan..."`.
- **Response Handling:** On HTTP 200, the frontend parses `result.data` and populates the `#statusNotification` card with the unique `Plan ID` and parameter summary grid.
- **Error Handling:** On HTTP 400/500, field-specific error messages are mapped to inputs with red borders without breaking the UI.
