import { NextResponse } from "next/server";

export async function POST(request) {
  try {
    const body = await request.json();

    const {
      researchQuestion,
      targetMarket,
      geography,
      customGeography,
      timeframe,
      competitors,
    } = body;

    // Server-side validation
    const errors = {};

    if (!researchQuestion || !researchQuestion.trim()) {
      errors.researchQuestion = "Research question is required.";
    }

    if (!targetMarket || !targetMarket.trim()) {
      errors.targetMarket = "Target market is required.";
    }

    if (!geography) {
      errors.geography = "Geography is required.";
    } else if (geography === "Other" && (!customGeography || !customGeography.trim())) {
      errors.customGeography = "Please specify your custom geography.";
    }

    if (Object.keys(errors).length > 0) {
      return NextResponse.json(
        { success: false, errors, message: "Validation failed on the server." },
        { status: 400 }
      );
    }

    // Determine final geography string
    const finalGeography = geography === "Other" ? customGeography.trim() : geography;

    // Backend configurable defaults for McKinsey AI Engine
    const backendDefaults = {
      deliverableFormat: "Strategy Brief",
      reportDepth: "Standard",
      sourcePreference: "Public Sources",
      reportPurpose: "Internal Review",
    };

    // Complete research query plan payload (Prepared for future Planner Agent)
    const researchPlanRequest = {
      id: `PLAN-${Date.now()}`,
      createdAt: new Date().toISOString(),
      // User inputs
      researchQuestion: researchQuestion.trim(),
      targetMarket: targetMarket.trim(),
      geography: finalGeography,
      timeframe: timeframe || "Last 3 Years",
      competitors: competitors ? competitors.trim() : "None specified",
      // Configurable backend defaults
      ...backendDefaults,
      // Future Planner Agent integration status
      agentStatus: "READY_FOR_PLANNER_AGENT",
    };

    /*
     * NOTE FOR FUTURE PLANNER AGENT INTEGRATION:
     * In the next phase of this project, this is where the Planner Agent
     * will be initialized with `researchPlanRequest`.
     * The Planner Agent will decompose this query into sub-tasks:
     * 1. Industry trend breakdown
     * 2. Competitor benchmarking
     * 3. Strategic synthesis & recommendation generation
     */

    return NextResponse.json(
      {
        success: true,
        message: "Research request validated and saved successfully.",
        data: researchPlanRequest,
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        message: "Server error processing research request.",
        error: error.message,
      },
      { status: 500 }
    );
  }
}
