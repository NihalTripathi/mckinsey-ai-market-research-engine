/**
 * McKinsey | Strategy Engine — AI Market Research
 * Client-Side Application Logic Connected to FastAPI Backend
 */

const API_BASE_URL = 'https://mckinsey-ai-market-research-engine-9ez9.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const researchForm = document.getElementById('researchForm');
  const btnSubmit = document.getElementById('btnSubmit');
  const btnResetForm = document.getElementById('btnResetForm');

  // Input Fields
  const inputQuestion = document.getElementById('researchQuestion');
  const inputTargetMarket = document.getElementById('targetMarket');
  const selectGeography = document.getElementById('geography');
  const customGeoContainer = document.getElementById('customGeographyContainer');
  const inputCustomGeography = document.getElementById('customGeography');
  const selectTimeframe = document.getElementById('timeframe');
  const inputCompetitors = document.getElementById('competitors');

  // Error Containers
  const errQuestion = document.getElementById('errResearchQuestion');
  const errTargetMarket = document.getElementById('errTargetMarket');
  const errGeography = document.getElementById('errGeography');
  const errCustomGeography = document.getElementById('errCustomGeography');

  // Notification Banner
  const statusNotification = document.getElementById('statusNotification');
  const statusPlanId = document.getElementById('statusPlanId');
  const statusSummaryGrid = document.getElementById('statusSummaryGrid');

  // Navigation Links & Modal Elements
  const navResearch = document.getElementById('navResearch');
  const navSampleReport = document.getElementById('navSampleReport');
  const navMethodology = document.getElementById('navMethodology');
  const infoModal = document.getElementById('infoModal');
  const modalTitle = document.getElementById('modalTitle');
  const modalBody = document.getElementById('modalBody');
  const modalClose = document.getElementById('modalClose');

  selectGeography.addEventListener('change', () => {
    if (selectGeography.value === 'Other') {
      customGeoContainer.classList.remove('hidden');
      inputCustomGeography.focus();
    } else {
      customGeoContainer.classList.add('hidden');
      inputCustomGeography.value = '';
      clearFieldError(inputCustomGeography, errCustomGeography);
    }
    clearFieldError(selectGeography, errGeography);
  });

  function showFieldError(inputEl, errorEl, message) {
    inputEl.classList.add('is-invalid');
    errorEl.textContent = message;
    errorEl.classList.add('visible');
  }

  function clearFieldError(inputEl, errorEl) {
    inputEl.classList.remove('is-invalid');
    errorEl.textContent = '';
    errorEl.classList.remove('visible');
  }

  inputQuestion.addEventListener('input', () => clearFieldError(inputQuestion, errQuestion));
  inputTargetMarket.addEventListener('input', () => clearFieldError(inputTargetMarket, errTargetMarket));
  inputCustomGeography.addEventListener('input', () => clearFieldError(inputCustomGeography, errCustomGeography));

  function validateForm() {
    let isValid = true;
    if (!inputQuestion.value.trim()) {
      showFieldError(inputQuestion, errQuestion, 'Research question is required.');
      isValid = false;
    } else {
      clearFieldError(inputQuestion, errQuestion);
    }

    if (!inputTargetMarket.value.trim()) {
      showFieldError(inputTargetMarket, errTargetMarket, 'Target market is required.');
      isValid = false;
    } else {
      clearFieldError(inputTargetMarket, errTargetMarket);
    }

    if (!selectGeography.value) {
      showFieldError(selectGeography, errGeography, 'Please select a geography.');
      isValid = false;
    } else if (selectGeography.value === 'Other' && !inputCustomGeography.value.trim()) {
      showFieldError(inputCustomGeography, errCustomGeography, 'Please specify custom country or region.');
      isValid = false;
    } else {
      clearFieldError(selectGeography, errGeography);
      clearFieldError(inputCustomGeography, errCustomGeography);
    }
    return isValid;
  }

  // Form Submission Handler -> Connects directly to Python FastAPI (/api/research-jobs)
  researchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    const finalGeo = selectGeography.value === 'Other'
      ? inputCustomGeography.value.trim()
      : selectGeography.value;

    const competitorsText = inputCompetitors.value.trim();
    const fullQuestion = competitorsText
      ? `${inputQuestion.value.trim()} (Focus competitors: ${competitorsText})`
      : inputQuestion.value.trim();

    // Payload matching FastAPI ResearchJobRequest schema
    const payload = {
      question: fullQuestion,
      geography: finalGeo,
      timeframe: selectTimeframe.value,
      industry: inputTargetMarket.value.trim(),
      per_task: 3
    };

    const originalBtnHtml = btnSubmit.innerHTML;
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `
      <span style="display:inline-block; width:14px; height:14px; border:2px solid rgba(255,255,255,0.3); border-top-color:#fff; border-radius:50%; animation:spin 0.6s linear infinite; margin-right:6px;"></span>
      <span>Running AI Agents (Takes ~30-60s)...</span>
    `;

    try {
      const response = await fetch(`${API_BASE_URL}/api/research-jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      if (response.ok && result.status === 'completed') {
        console.log('[FastAPI] Research Completed:', result);
        renderLiveReport(result, payload, competitorsText);
      } else {
        alert(result.detail || 'Error running AI research pipeline.');
      }
    } catch (error) {
      console.error('[Network Error]:', error);
      alert('AI Research Server se connect nahi ho paaya. Agar server sleep mode mein tha toh 40 second baad dubara Submit dabayein.');
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = originalBtnHtml;
    }
  });

  function renderLiveReport(result, payload, competitorsText) {
    statusPlanId.innerHTML = `
      Job ID: <strong>${escapeHtml(result.job_id)}</strong> &bull; Status: <strong>COMPLETED</strong>
      <a href="${API_BASE_URL}/api/reports/${encodeURIComponent(result.job_id)}/pdf" target="_blank"
         style="margin-left:14px; padding:6px 12px; background:#0F172A; color:#fff; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600;">
        Download Executive PDF Brief
      </a>
    `;

    const report = result.report || {};
    const execSummary = report.executive_summary || 'Executive brief generated successfully.';
    const keyFindings = Array.isArray(report.key_findings) ? report.key_findings : [];
    const recommendations = Array.isArray(report.recommendations) ? report.recommendations : [];

    statusSummaryGrid.innerHTML = `
      <div>
        <span class="summary-field-title">Research Question</span>
        <span class="summary-field-value">${escapeHtml(payload.question)}</span>
      </div>
      <div>
        <span class="summary-field-title">Target Industry & Geography</span>
        <span class="summary-field-value">${escapeHtml(payload.industry)} &bull; ${escapeHtml(payload.geography)}</span>
      </div>
      <div>
        <span class="summary-field-title">Timeframe & Competitors</span>
        <span class="summary-field-value">${escapeHtml(payload.timeframe)} | ${escapeHtml(competitorsText || 'Auto-detected')}</span>
      </div>
      <div style="grid-column: 1 / -1; margin-top: 12px; padding-top: 12px; border-top: 1px solid #E2E8F0;">
        <span class="summary-field-title" style="color:#0F172A; font-size:14px;">Executive Summary</span>
        <p style="margin-top:6px; line-height:1.6; color:#1E293B;">${escapeHtml(execSummary)}</p>
      </div>
      ${keyFindings.length ? `
      <div style="grid-column: 1 / -1; margin-top: 8px;">
        <span class="summary-field-title" style="color:#0F172A; font-size:14px;">Key Strategic Findings</span>
        <ul style="margin:6px 0 0 18px; line-height:1.6; color:#334155;">
          ${keyFindings.map(item => `<li>${escapeHtml(typeof item === 'string' ? item : (item.finding || item.claim || JSON.stringify(item)))}</li>`).join('')}
        </ul>
      </div>` : ''}
      ${recommendations.length ? `
      <div style="grid-column: 1 / -1; margin-top: 8px;">
        <span class="summary-field-title" style="color:#0F172A; font-size:14px;">Strategic Recommendations</span>
        <ul style="margin:6px 0 0 18px; line-height:1.6; color:#334155;">
          ${recommendations.map(item => `<li>${escapeHtml(typeof item === 'string' ? item : (item.recommendation || item.action || JSON.stringify(item)))}</li>`).join('')}
        </ul>
      </div>` : ''}
    `;

    statusNotification.classList.remove('hidden');
    statusNotification.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  btnResetForm.addEventListener('click', () => {
    researchForm.reset();
    selectGeography.value = '';
    customGeoContainer.classList.add('hidden');
    selectTimeframe.value = 'Last 3 Years (Default)';
    statusNotification.classList.add('hidden');
    clearFieldError(inputQuestion, errQuestion);
    clearFieldError(inputTargetMarket, errTargetMarket);
    clearFieldError(selectGeography, errGeography);
    clearFieldError(inputCustomGeography, errCustomGeography);
    inputQuestion.focus();
  });

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  navResearch.addEventListener('click', (e) => {
    e.preventDefault();
    setActiveNav(navResearch);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  navSampleReport.addEventListener('click', (e) => {
    e.preventDefault();
    setActiveNav(navSampleReport);
    openModal(
      'Sample Strategic Report Preview',
      `
        <p>Connected live to the <strong>LangGraph Multi-Agent Research Pipeline</strong>:</p>
        <ul style="margin: 12px 0 12px 20px; line-height: 1.8;">
          <li><strong>Market Sizing & TAM:</strong> Bottom-up and top-down revenue opportunity modeling.</li>
          <li><strong>Competitive Landscape:</strong> Direct and indirect competitor positioning matrix.</li>
          <li><strong>SWOT + Porter's Five Forces:</strong> Structural industry profitability evaluation.</li>
          <li><strong>Executive Strategy Synthesis:</strong> Condensed boardroom recommendations & PDF Brief.</li>
        </ul>
      `
    );
  });

  navMethodology.addEventListener('click', (e) => {
    e.preventDefault();
    setActiveNav(navMethodology);
    openModal(
      'Consulting Research Methodology',
      `
        <p>The <strong>McKinsey Strategy Engine</strong> follows a multi-agent problem-solving architecture:</p>
        <ol style="margin: 12px 0 12px 20px; line-height: 1.8;">
          <li><strong>Planner Agent:</strong> Breaks down research questions into structured sub-tasks.</li>
          <li><strong>Search & Extraction Agents:</strong> Gathers live web evidence via Tavily & Gemini.</li>
          <li><strong>Validation & Synthesis Agents:</strong> Verifies claims and generates an executive PDF brief.</li>
        </ol>
      `
    );
  });

  function setActiveNav(selectedItem) {
    [navResearch, navSampleReport, navMethodology].forEach(item => item.classList.remove('active'));
    selectedItem.classList.add('active');
  }

  function openModal(title, content) {
    modalTitle.textContent = title;
    modalBody.innerHTML = content;
    infoModal.classList.remove('hidden');
  }

  modalClose.addEventListener('click', () => {
    infoModal.classList.add('hidden');
    setActiveNav(navResearch);
  });

  infoModal.addEventListener('click', (e) => {
    if (e.target === infoModal) {
      infoModal.classList.add('hidden');
      setActiveNav(navResearch);
    }
  });
});

const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleSheet);