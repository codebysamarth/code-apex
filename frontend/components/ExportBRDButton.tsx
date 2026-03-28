'use client';

import React, { useState } from 'react';
import { BRDState } from '@/lib/types';
import { cn } from '@/lib/utils';
import { FileText, Loader2, Check } from 'lucide-react';

interface ExportBRDButtonProps {
  data: BRDState;
}

export default function ExportBRDButton({ data }: ExportBRDButtonProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDone, setIsDone] = useState(false);

  const handleExportPDF = () => {
    setIsGenerating(true);

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      alert("Please allow popups to export the BRD.");
      setIsGenerating(false);
      return;
    }

    const domain = data.domain || 'software';
    
    const domainHeaders: Record<string, string> = {
      software: 'Business Requirements Document (BRD)',
      healthcare: 'Clinical Systems Specification',
      mechanical: 'Mechanical Design Specification',
      business: 'Business Strategy Roadmap'
    };
    const domainThemes: Record<string, { main: string, dark: string, light: string }> = {
      software: { main: '#4A5D5F', dark: '#2D3E40', light: '#DDE5DD' },
      healthcare: { main: '#38A169', dark: '#276749', light: '#F0FFF4' },
      mechanical: { main: '#D69E2E', dark: '#975A16', light: '#FFFFF0' },
      business: { main: '#3182CE', dark: '#2B6CB0', light: '#EBF8FF' },
    };
    const domainGoals: Record<string, string> = {
      software: 'Transform extraction logic into structured multi-layer requirements',
      healthcare: 'Standardize clinical specifications while ensuring patient safety and compliance',
      mechanical: 'Optimize mechanical specifications with strict tolerances and material standards',
      business: 'Align strategic business objectives with actionable KPIs and market drivers'
    };

    const theme = domainThemes[domain] || domainThemes['software'];
    const documentTitle = domainHeaders[domain] || domainHeaders['software'];
    const projectGoal = domainGoals[domain] || domainGoals['software'];
    
    const outputList = domain === 'software' ? [
      'Structured BRD (Functional, Non Functional, Stakeholders, Decisions, Timeline)',
      'Source Trace (Requirement → Evidence Chain)',
      'Actionable Risk Mitigation & Gaps summary'
    ] : [
      'Industry-Specific Structured Specification',
      'Industrial Risk & Regulatory Mitigation',
      'Domain Awareness & Confidence Validation'
    ];

    const html = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>ApexBRD Infographic Report - ${domain.toUpperCase()}</title>
          <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
            :root {
              --theme-main: ${theme.main};
              --theme-dark: ${theme.dark};
              --theme-light: ${theme.light};
            }
            body { 
              font-family: 'Inter', sans-serif; 
              background-color: #f0f2f0; 
              padding: 40px; 
              margin: 0;
              color: #1a202c;
              -webkit-print-color-adjust: exact;
            }

            .container {
              max-width: 1000px;
              margin: 0 auto;
              background: white;
              border-radius: 12px;
              overflow: hidden;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }

            /* Header Section */
            .main-header {
              background-color: var(--theme-dark);
              color: white;
              padding: 28px;
              text-align: center;
              text-transform: uppercase;
              letter-spacing: 0.15em;
            }
            .main-header h1 { margin: 0; font-size: 28px; font-weight: 800; }
            
            .sub-header {
              background-color: white;
              padding: 14px;
              text-align: center;
              border-bottom: 2px solid #E2E8F0;
              font-weight: 700;
              color: var(--theme-dark);
              font-size: 16px;
              margin-bottom: 0;
            }

            .content-padding { padding: 30px; }

            /* Section Cards */
            .section-card {
              border: 1.5px solid #E2E8F0;
              border-radius: 10px;
              overflow: hidden;
              background-color: white;
              margin-bottom: 24px;
              page-break-inside: avoid;
            }

            .section-header {
              background-color: var(--theme-main);
              color: white;
              padding: 12px 20px;
              font-size: 14px;
              font-weight: 800;
              text-transform: uppercase;
              letter-spacing: 0.05em;
              display: flex;
              align-items: center;
            }

            /* Project Overview Styles */
            .overview-card {
              background-color: white;
              border: 1.5px solid #CBD5E0;
            }
            .overview-content { padding: 20px; }
            .overview-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
            .overview-row:last-child { margin-bottom: 0; }
            .overview-icon { font-size: 16px; width: 24px; text-align: center; }
            .overview-text b { color: var(--theme-dark); margin-right: 5px; }

            /* Bento Grid */
            .bento-grid {
              display: grid;
              grid-template-columns: 1fr 1fr;
              gap: 24px;
              margin-top: 24px;
            }

            table {
              width: 100%;
              border-collapse: collapse;
              font-size: 12px;
            }
            th {
              background-color: var(--theme-light);
              color: var(--theme-dark);
              text-align: left;
              padding: 10px 16px;
              text-transform: uppercase;
              font-weight: 800;
              font-size: 10px;
              border-bottom: 1px solid #CBD5E0;
            }
            td {
              padding: 12px 16px;
              border-bottom: 1px solid #EDF2F7;
              color: #4A5568;
              font-weight: 500;
              vertical-align: top;
            }

            /* Checks & List */
            .check-list { padding: 20px; }
            .check-item { display: flex; gap: 12px; margin-bottom: 14px; font-size: 12px; font-weight: 600; color: #4A5568; line-height: 1.5; }
            .check-icon { color: var(--theme-light); font-weight: 900; shrink: 0; }

            .final-outputs {
              background-color: var(--theme-main);
              color: white;
              padding: 30px;
              border-radius: 10px;
              margin-top: 20px;
              page-break-inside: avoid;
            }
            .final-outputs h3 { margin: 0 0 18px 0; font-size: 15px; text-transform: uppercase; letter-spacing: 0.1em; color: white; }
            .output-row { display: flex; align-items: center; gap: 12px; font-size: 13px; font-weight: 700; margin-bottom: 10px; }
            .output-row:last-child { margin-bottom: 0; }

            .confidential-footer {
              text-align: center;
              margin-top: 40px;
              color: #718096;
              font-size: 10px;
              font-weight: 800;
              letter-spacing: 0.25em;
              text-transform: uppercase;
            }

            @media print {
              body { background: white; padding: 0.5cm; }
              .container { box-shadow: none; border-radius: 0; max-width: 100%; border: 1px solid #eee; }
              @page { margin: 1cm; size: auto; }
            }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="main-header">
              <h1>${documentTitle}</h1>
            </div>
            <div class="sub-header">
              AI-Powered Requirements Analysis System - ${domain.toUpperCase()} MODE
            </div>

            <div class="content-padding">
              <!-- Project Overview -->
              <div class="section-card overview-card">
                <div class="section-header">Project Overview</div>
                <div class="overview-content">
                  <div class="overview-row">
                    <span class="overview-icon">🎯</span>
                    <span class="overview-text"><b>Goal:</b> ${projectGoal}</span>
                  </div>
                  <div class="overview-row">
                    <span class="overview-icon">📅</span>
                    <span class="overview-text"><b>Timeline:</b> ${data.timeline && data.timeline.length > 0 ? data.timeline.length + ' Core Phases' : '6 Weeks Standard'}</span>
                  </div>
                  <div class="overview-row">
                    <span class="overview-icon">📊</span>
                    <span class="overview-text"><b>Success Metric:</b> 90% automated requirement completeness and traceability</span>
                  </div>
                  ${data.domain_data?.compliance_check ? `
                  <div class="overview-row">
                    <span class="overview-icon">🛡️</span>
                    <span class="overview-text"><b>Compliance (${data.domain_data.compliance_check.status.toUpperCase()}):</b> ${data.domain_data.compliance_check.standard}</span>
                  </div>` : ''}
                </div>
              </div>

              <div class="bento-grid">
                ${domain === 'software' ? `
                  <!-- Functional -->
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header">Functional Requirements</div>
                    <table>
                      <thead><tr><th style="width: 40px;">ID</th><th style="width: 100px;">Feature</th><th>Description</th></tr></thead>
                      <tbody>
                        ${data.functional.map(req => `
                          <tr>
                            <td style="color: #718096; font-family: monospace;">${req.id}</td>
                            <td style="font-weight: 800;">${req.title}</td>
                            <td style="font-size: 11px;">${req.description.substring(0, 100)}${req.description.length > 100 ? '...' : ''}</td>
                          </tr>
                        `).join('') || '<tr><td colspan="3">Processing requirements...</td></tr>'}
                      </tbody>
                    </table>
                  </div>

                  <!-- NFR -->
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header">Non-Functional Requirements</div>
                    <table>
                      <thead><tr><th style="width: 80px;">Category</th><th>Requirement</th></tr></thead>
                      <tbody>
                        ${data.nfr.map(req => `
                          <tr>
                            <td style="font-weight: 800; color: var(--theme-dark);">${req.category}</td>
                            <td style="font-size: 11px;">${req.description}</td>
                          </tr>
                        `).join('') || '<tr><td colspan="2">Identifying specifications...</td></tr>'}
                      </tbody>
                    </table>
                  </div>

                  <!-- Stakeholders -->
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header">Stakeholders</div>
                    <table>
                      <thead><tr><th>Identity</th><th>Core Role</th></tr></thead>
                      <tbody>
                        ${data.stakeholders.map(s => `
                          <tr><td style="font-weight: 800;">${s.name}</td><td style="font-size: 11px;">${s.role}</td></tr>
                        `).join('') || '<tr><td colspan="2">Identifying stakeholders...</td></tr>'}
                      </tbody>
                    </table>
                  </div>

                  <!-- Decisions -->
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header">Decisions & Approvals</div>
                    <table>
                      <thead><tr><th>Owner</th><th>Approval Required</th></tr></thead>
                      <tbody>
                        ${data.decisions.map(d => `
                          <tr><td style="font-size: 11px;">${d.decision.substring(0, 50)}...</td><td style="font-weight: 800; color: var(--theme-dark);">Pending</td></tr>
                        `).join('') || '<tr><td colspan="2">Analyzing major decisions...</td></tr>'}
                      </tbody>
                    </table>
                  </div>

                  <!-- Timeline -->
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header">Timeline & Milestones</div>
                    <table>
                      <thead><tr><th>Phase</th><th>Activity</th></tr></thead>
                      <tbody>
                        ${data.timeline.map(t => `
                          <tr><td style="font-weight: 800; text-transform: uppercase; font-size: 10px; width: 80px;">${t.phase}</td><td style="font-size: 11px;">${t.activity}</td></tr>
                        `).join('') || '<tr><td colspan="2">Planning milestones...</td></tr>'}
                      </tbody>
                    </table>
                  </div>

                  <!-- Risks -->
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header">Risks & Gaps Analysis</div>
                    <div class="check-list">
                      ${data.gaps.map(g => `
                        <div class="check-item"><span class="check-icon">✔</span><span>${g.description}</span></div>
                      `).join('') || '<div class="check-item"><span class="check-icon">✔</span><span>No high-risk architectural gaps detected.</span></div>'}
                    </div>
                  </div>
` : domain === 'healthcare' ? `
                  <div style="grid-column: span 2; margin-bottom: -10px;">
                     <h3 style="color: var(--theme-dark); font-size: 15px; font-weight: 800; text-transform: uppercase;">🏥 Healthcare Specifications & Parameters</h3>
                  </div>

                  ${Object.entries(data.domain_data?.sections || {}).map(([title, items]: [string, any]) => `
                    <div class="section-card" style="margin-bottom: 0;">
                      <div class="section-header">${title}</div>
                      <table>
                        <thead><tr><th>Parameter / Requirement</th><th>Priority</th></tr></thead>
                        <tbody>
                          ${Array.isArray(items) ? items.map((item: any) => `
                            <tr>
                              <td style="font-size: 11px;">
                                <b>${item.title || item.name || item.objective || 'Item'}</b><br/>
                                <span style="color: #4A5568; margin-top: 4px; display: inline-block;">${item.description || item.requirement || item.specification || ''}</span>
                                ${item.mitigation ? `<div style="margin-top: 8px; padding: 6px; background-color: #FFF5F5; border: 1px solid #FED7D7; border-radius: 4px; color: #C53030; font-weight: 700; font-size: 10px;">Mitigation: ${item.mitigation}</div>` : ''}
                              </td>
                              <td style="font-weight: 800; color: var(--theme-dark); width: 80px;">${item.priority || 'Normal'}</td>
                            </tr>
                          `).join('') : '<tr><td colspan="2">No parameters found</td></tr>'}
                        </tbody>
                      </table>
                    </div>
                  `).join('')}
                  <!-- Domain Specific Scores -->
                  ${data.domain_data?.domain_scores ? `
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header">Clinical Performance & Impact Analysis</div>
                    <table>
                      <thead><tr><th style="width: 150px;">Healthcare Metric</th><th style="width: 60px;">Score</th><th>Rationale</th></tr></thead>
                      <tbody>
                        ${Object.entries(data.domain_data.domain_scores).map(([key, score]: [string, any]) => `
                          <tr>
                            <td style="font-weight: 800; text-transform: uppercase;">${key.replace(/_/g, ' ')}</td>
                            <td style="font-size: 14px; font-weight: 900; color: var(--theme-dark);">${Math.round((score.value || score) * 100)}%</td>
                            <td style="font-size: 11px;">${score.rationale || 'Clinical validity score'}</td>
                          </tr>
                        `).join('')}
                      </tbody>
                    </table>
                  </div>` : ''}
                  <!-- Architectural Conflict Detection -->
                  ${data.domain_data?.innovation_metrics?.conflict_detection ? `
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header" style="background-color: #DD6B20;">Patient Safety & System Conflict Alert</div>
                    <div class="overview-content">
                       <p style="font-size: 12px; font-weight: 600; color: #C05621; margin: 0; line-height: 1.5;">
                         ${data.domain_data.innovation_metrics.conflict_detection}
                       </p>
                    </div>
                  </div>` : ''}
` : domain === 'mechanical' ? `
                  <div style="grid-column: span 2; margin-bottom: -10px;">
                     <h3 style="color: var(--theme-dark); font-size: 15px; font-weight: 800; text-transform: uppercase;">⚙️ Mechanical Engineering Parameters</h3>
                  </div>

                  ${Object.entries(data.domain_data?.sections || {}).map(([title, items]: [string, any]) => `
                    <div class="section-card" style="margin-bottom: 0;">
                      <div class="section-header">${title}</div>
                      <table>
                        <thead><tr><th>Parameter / Requirement</th><th>Priority</th></tr></thead>
                        <tbody>
                          ${Array.isArray(items) ? items.map((item: any) => `
                            <tr>
                              <td style="font-size: 11px;">
                                <b>${item.title || item.name || item.objective || 'Item'}</b><br/>
                                <span style="color: #4A5568; margin-top: 4px; display: inline-block;">${item.description || item.requirement || item.specification || ''}</span>
                                ${item.mitigation ? `<div style="margin-top: 8px; padding: 6px; background-color: #FFF5F5; border: 1px solid #FED7D7; border-radius: 4px; color: #C53030; font-weight: 700; font-size: 10px;">Mitigation: ${item.mitigation}</div>` : ''}
                              </td>
                              <td style="font-weight: 800; color: var(--theme-dark); width: 80px;">${item.priority || 'Normal'}</td>
                            </tr>
                          `).join('') : '<tr><td colspan="2">No parameters found</td></tr>'}
                        </tbody>
                      </table>
                    </div>
                  `).join('')}
                  <!-- Domain Specific Scores -->
                  ${data.domain_data?.domain_scores ? `
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header">Engineering Stress & Analysis</div>
                    <table>
                      <thead><tr><th style="width: 150px;">Engineering Metric</th><th style="width: 60px;">Score</th><th>Rationale</th></tr></thead>
                      <tbody>
                        ${Object.entries(data.domain_data.domain_scores).map(([key, score]: [string, any]) => `
                          <tr>
                            <td style="font-weight: 800; text-transform: uppercase;">${key.replace(/_/g, ' ')}</td>
                            <td style="font-size: 14px; font-weight: 900; color: var(--theme-dark);">${Math.round((score.value || score) * 100)}%</td>
                            <td style="font-size: 11px;">${score.rationale || 'Engineering integrity score'}</td>
                          </tr>
                        `).join('')}
                      </tbody>
                    </table>
                  </div>` : ''}
                  <!-- Architectural Conflict Detection -->
                  ${data.domain_data?.innovation_metrics?.conflict_detection ? `
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header" style="background-color: #E53E3E;">Structural Failure & Tolerance Alert</div>
                    <div class="overview-content">
                       <p style="font-size: 12px; font-weight: 600; color: #C53030; margin: 0; line-height: 1.5;">
                         ${data.domain_data.innovation_metrics.conflict_detection}
                       </p>
                    </div>
                  </div>` : ''}
` : domain === 'business' ? `
                  <div style="grid-column: span 2; margin-bottom: -10px;">
                     <h3 style="color: var(--theme-dark); font-size: 15px; font-weight: 800; text-transform: uppercase;">📊 Business Strategy & KPI Parameters</h3>
                  </div>

                  ${Object.entries(data.domain_data?.sections || {}).map(([title, items]: [string, any]) => `
                    <div class="section-card" style="margin-bottom: 0;">
                      <div class="section-header">${title}</div>
                      <table>
                        <thead><tr><th>Parameter / Requirement</th><th>Priority</th></tr></thead>
                        <tbody>
                          ${Array.isArray(items) ? items.map((item: any) => `
                            <tr>
                              <td style="font-size: 11px;">
                                <b>${item.title || item.name || item.objective || 'Item'}</b><br/>
                                <span style="color: #4A5568; margin-top: 4px; display: inline-block;">${item.description || item.requirement || item.specification || ''}</span>
                                ${item.mitigation ? `<div style="margin-top: 8px; padding: 6px; background-color: #FFF5F5; border: 1px solid #FED7D7; border-radius: 4px; color: #C53030; font-weight: 700; font-size: 10px;">Mitigation: ${item.mitigation}</div>` : ''}
                              </td>
                              <td style="font-weight: 800; color: var(--theme-dark); width: 80px;">${item.priority || 'Normal'}</td>
                            </tr>
                          `).join('') : '<tr><td colspan="2">No parameters found</td></tr>'}
                        </tbody>
                      </table>
                    </div>
                  `).join('')}
                  <!-- Domain Specific Scores -->
                  ${data.domain_data?.domain_scores ? `
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header">Financial & Strategic Analysis</div>
                    <table>
                      <thead><tr><th style="width: 150px;">Business Metric</th><th style="width: 60px;">Score</th><th>Rationale</th></tr></thead>
                      <tbody>
                        ${Object.entries(data.domain_data.domain_scores).map(([key, score]: [string, any]) => `
                          <tr>
                            <td style="font-weight: 800; text-transform: uppercase;">${key.replace(/_/g, ' ')}</td>
                            <td style="font-size: 14px; font-weight: 900; color: var(--theme-dark);">${Math.round((score.value || score) * 100)}%</td>
                            <td style="font-size: 11px;">${score.rationale || 'Strategic validity score'}</td>
                          </tr>
                        `).join('')}
                      </tbody>
                    </table>
                  </div>` : ''}
                  <!-- Architectural Conflict Detection -->
                  ${data.domain_data?.innovation_metrics?.conflict_detection ? `
                  <div class="section-card" style="margin-bottom: 0;">
                    <div class="section-header" style="background-color: #DD6B20;">Market & Strategic Alignment Risk</div>
                    <div class="overview-content">
                       <p style="font-size: 12px; font-weight: 600; color: #C05621; margin: 0; line-height: 1.5;">
                         ${data.domain_data.innovation_metrics.conflict_detection}
                       </p>
                    </div>
                  </div>` : ''}
` : ''}
              </div>

              <!-- Final Outputs -->
              <div class="final-outputs">
                <h3>Final System Outputs</h3>
                ${outputList.map(out => `
                  <div class="output-row"><span class="check-icon" style="color: white;">✔</span> ${out}</div>
                `).join('')}
              </div>

              <div class="confidential-footer">
                GENERATED BY APEXBRD INTELLIGENCE ENGINE • CONFIDENTIAL
              </div>
            </div>
          </div>

          <script>
            window.onload = function() {
              setTimeout(() => { window.print(); }, 800);
            };
          </script>
        </body>
      </html>
    `;

    printWindow.document.write(html);
    printWindow.document.close();

    setIsDone(true);
    setTimeout(() => setIsDone(false), 3000);
    setIsGenerating(false);
  };

  return (
    <button
      onClick={handleExportPDF}
      disabled={isGenerating}
      className={cn(
        "flex items-center gap-2.5 bg-white border border-[#E9E9E7] rounded-lg px-4 py-2 text-[13.5px] font-bold text-[#37352F] shadow-sm hover:bg-[#F7F7F5] active:scale-[0.98] transition-all disabled:opacity-50",
        isDone && "border-green-200 bg-green-50 text-green-700"
      )}
    >
      {isGenerating ? (
        <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      ) : isDone ? (
        <Check className="w-4 h-4" />
      ) : (
        <FileText className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" />
      )}
      {isGenerating ? "Rendering..." : isDone ? "Ready" : "Export BRD"}
    </button>
  );
}
