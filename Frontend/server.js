const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static frontend assets from 'public' folder
app.use(express.static(path.join(__dirname, 'public')));

/**
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'McKinsey AI Market Research & Strategy Engine - Frontend Server',
    timestamp: new Date().toISOString()
  });
});

/**
 * Research Query Submission Endpoint
 * Receives the 5 research configuration parameters from the frontend.
 * Validates inputs, injects configurable defaults, and prepares the
 * payload for future LangGraph / Planner Agent orchestration.
 */
app.post('/api/research', (req, res) => {
  try {
    const {
      researchQuestion,
      targetMarket,
      geography,
      customGeography,
      timeframe,
      competitors
    } = req.body;

    // Server-side validation
    const errors = {};

    if (!researchQuestion || !researchQuestion.trim()) {
      errors.researchQuestion = 'Research question is required.';
    }

    if (!targetMarket || !targetMarket.trim()) {
      errors.targetMarket = 'Target market is required.';
    }

    if (!geography || !geography.trim()) {
      errors.geography = 'Geography is required.';
    } else if (geography === 'Other' && (!customGeography || !customGeography.trim())) {
      errors.customGeography = 'Please enter a custom country or region.';
    }

    if (Object.keys(errors).length > 0) {
      return res.status(400).json({
        success: false,
        message: 'Server-side validation failed.',
        errors
      });
    }

    const finalGeography = geography === 'Other' ? customGeography.trim() : geography.trim();

    // Configurable McKinsey Strategy Engine Backend Defaults
    const backendDefaults = {
      deliverableFormat: 'Strategy Brief',
      reportDepth: 'Standard (12 Analyses)',
      sourcePreference: 'Public & Verified Secondary Sources',
      reportPurpose: 'Internal Strategic Review'
    };

    // Construct the structured research plan request
    // This is the clean handover contract for the next team member's LangGraph agents
    const researchPlanPayload = {
      id: `PLAN-${Date.now()}`,
      createdAt: new Date().toISOString(),
      inputs: {
        researchQuestion: researchQuestion.trim(),
        targetMarket: targetMarket.trim(),
        geography: finalGeography,
        timeframe: timeframe || 'Last 3 Years (Default)',
        competitors: competitors && competitors.trim() ? competitors.trim() : 'None specified'
      },
      systemDefaults: backendDefaults,
      // Target 12 strategic analyses scope
      plannedAnalyses: [
        'Market Sizing & TAM',
        'Competitive Landscape',
        'Customer Personas',
        'Industry Trends (5-Year)',
        'SWOT + Porter\'s Five Forces',
        'Pricing Strategy (3-Tier)',
        'Go-to-Market Plan',
        'Customer Journey Mapping',
        'Financial Modeling (3-Year)',
        'Risk Assessment (15 Risks)',
        'Market Entry Strategy (12-Month)',
        'Executive Strategy Synthesis'
      ],
      // Integration status flag
      agentStatus: 'READY_FOR_LANGGRAPH_INTEGRATION',
      workflowPending: true
    };

    /*
     * =========================================================================
     * NOTE FOR NEXT TEAM MEMBER (LANGGRAPH / PLANNER AGENT INTEGRATION):
     * =========================================================================
     * In the next development phase, connect your LangGraph workflow here:
     * 
     * const workflowResult = await runLangGraphResearchWorkflow(researchPlanPayload);
     * return res.json({ success: true, result: workflowResult });
     * 
     * Currently, the system returns a verified pending-integration response
     * without generating fake or hardcoded research results.
     * =========================================================================
     */

    console.log('[API] New Research Request Received & Validated:', researchPlanPayload.id);

    return res.status(200).json({
      success: true,
      message: 'Research request saved locally. Backend integration pending.',
      data: researchPlanPayload
    });

  } catch (error) {
    console.error('[API Error]:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error processing research request.',
      error: error.message
    });
  }
});

// Fallback route to serve index.html for SPA-style navigation
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start Express server
app.listen(PORT, () => {
  console.log(`================================================================`);
  console.log(` McKinsey AI Market Research & Strategy Engine (Frontend Server)`);
  console.log(` Running locally at: http://localhost:${PORT}`);
  console.log(` Architecture: Node.js + Express + Vanilla HTML/CSS/JS`);
  console.log(`================================================================`);
});
