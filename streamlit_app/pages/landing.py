"""
Landing page — EduPath AI marketing homepage.

Features:
  1. Sticky top navigation
  2. Hero section with AI-generated Vector Multi-Agent Network illustration + Live Counselor Preview
  3. The Challenge / Problem section with comparative visual infographics
  4. 4-step process flow
  5. 9-agent workforce architecture
  6. Personalization demo
  7. Core features grid
  8. Trust & sources grounding
  9. Final CTA
  10. Footer
"""
from __future__ import annotations

import streamlit as st
from components.common import render_html


def _hide_streamlit_chrome() -> None:
    render_html(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        [data-testid="stStatusWidget"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        footer { display: none !important; }
        </style>
        """
    )


def render_navigation() -> None:
    render_html(
        """
        <nav class="ep-landing-nav">
          <div class="ep-landing-nav-inner">
            <div class="ep-landing-nav-brand">
              <div class="ep-brand-mark" style="width:34px;height:34px;font-size:0.95rem;border-radius:10px;">E</div>
              <span class="ep-landing-nav-brand-name">EduPath AI</span>
            </div>
            <div class="ep-landing-nav-links">
              <a href="#how-it-works" class="ep-nav-link">How It Works</a>
              <a href="#agents" class="ep-nav-link">AI Agents</a>
              <a href="#features" class="ep-nav-link">Features</a>
              <a href="#trust" class="ep-nav-link">Trust & Sources</a>
            </div>
            <div class="ep-landing-nav-actions">
              <a href="?page=login" class="ep-nav-btn-secondary">Sign In</a>
              <a href="?page=login" class="ep-nav-btn-primary">Get Started Free →</a>
            </div>
          </div>
        </nav>
        """
    )


def render_hero() -> None:
    render_html(
        """
        <section class="ep-hero-section">
          <div class="ep-hero-inner">
            <div class="ep-hero-text">
              <div class="ep-eyebrow" style="margin-bottom:1.25rem;">✦ AI-POWERED STUDY ABROAD COUNSELING</div>
              <h1 class="ep-hero-headline">
                Your AI-powered<br>
                <span class="ep-gradient-text">path to studying abroad.</span>
              </h1>
              <p class="ep-hero-sub">
                Meet your personal team of 9 coordinated AI agents. EduPath AI analyzes your academic profile, discovers top universities & funding, matches faculty research advisors, and builds your application strategy.
              </p>
              <div class="ep-hero-cta-group">
                <a href="?page=login" class="ep-btn-primary-lg">Start Free Counseling →</a>
                <a href="#how-it-works" class="ep-btn-secondary-lg">Explore How It Works ↓</a>
              </div>
              <div style="display: flex; gap: 1.5rem; margin-top: 2rem; align-items: center; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; color: #64748B; font-weight: 500;">
                  <span style="color: #16A34A; font-weight: 700;">✓</span> 100% Free for Students
                </div>
                <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; color: #64748B; font-weight: 500;">
                  <span style="color: #16A34A; font-weight: 700;">✓</span> 9 Specialist Agents
                </div>
                <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; color: #64748B; font-weight: 500;">
                  <span style="color: #16A34A; font-weight: 700;">✓</span> Grounded in Real Data
                </div>
              </div>
            </div>

            <div class="ep-hero-visual">
              <div style="position: relative;">
                <!-- Decorative SVG Background Aura -->
                <svg style="position: absolute; top: -30px; left: -30px; width: 420px; height: 420px; z-index: 0; pointer-events: none; opacity: 0.6;" viewBox="0 0 400 400" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="200" cy="200" r="180" stroke="url(#paint0_linear)" stroke-width="1.5" stroke-dasharray="6 6"/>
                  <circle cx="200" cy="200" r="120" stroke="url(#paint1_linear)" stroke-width="1.5"/>
                  <circle cx="200" cy="20" r="12" fill="#4F46E5" fill-opacity="0.15"/>
                  <circle cx="380" cy="200" r="10" fill="#7C3AED" fill-opacity="0.2"/>
                  <circle cx="200" cy="380" r="14" fill="#16A34A" fill-opacity="0.15"/>
                  <circle cx="20" cy="200" r="8" fill="#F59E0B" fill-opacity="0.2"/>
                  <defs>
                    <linearGradient id="paint0_linear" x1="0" y1="0" x2="400" y2="400" gradientUnits="userSpaceOnUse">
                      <stop stop-color="#4F46E5" stop-opacity="0.3"/>
                      <stop offset="1" stop-color="#7C3AED" stop-opacity="0.05"/>
                    </linearGradient>
                    <linearGradient id="paint1_linear" x1="80" y1="80" x2="320" y2="320" gradientUnits="userSpaceOnUse">
                      <stop stop-color="#7C3AED" stop-opacity="0.4"/>
                      <stop offset="1" stop-color="#4F46E5" stop-opacity="0.1"/>
                    </linearGradient>
                  </defs>
                </svg>

                <!-- Live Agent Preview Card -->
                <div class="ep-preview-card" style="position: relative; z-index: 1;">
                  <div class="ep-preview-card-header">
                    <div class="ep-preview-dot red"></div>
                    <div class="ep-preview-dot yellow"></div>
                    <div class="ep-preview-dot green"></div>
                    <span class="ep-preview-title">EduPath AI — Multi-Agent Live Workforce</span>
                  </div>
                  <div class="ep-preview-body">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                      <div>
                        <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Active Intake Profile</div>
                        <div style="font-size: 0.98rem; font-weight: 800; color: #0F172A;">Computer Science · PhD</div>
                      </div>
                      <span class="ep-badge success" style="font-size: 0.75rem;">94% Fit Score</span>
                    </div>

                    <div class="ep-preview-score-row">
                      <span class="ep-preview-label">Admission Match Strength</span>
                      <span class="ep-preview-score">94%</span>
                    </div>
                    <div class="ep-preview-bar-track"><div class="ep-preview-bar-fill" style="width:94%"></div></div>

                    <div class="ep-preview-checks" style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.65rem 0.85rem; margin-bottom: 0.9rem;">
                      <div class="ep-preview-check">✓ Academic GPA verified (3.85 / 4.0)</div>
                      <div class="ep-preview-check">✓ 3 Fully-Funded RA/TA Assistantships found</div>
                      <div class="ep-preview-check">✓ 5 Faculty Research Advisors aligned</div>
                    </div>

                    <div class="ep-preview-agents-label">Active Agent Execution</div>
                    <div class="ep-preview-agent-row">
                      <div class="ep-preview-agent-dot dot-green"></div>
                      <span class="ep-preview-agent-name">Profile Analyst</span>
                      <span class="ep-preview-agent-status status-done">Done</span>
                    </div>
                    <div class="ep-preview-agent-row">
                      <div class="ep-preview-agent-dot dot-green"></div>
                      <span class="ep-preview-agent-name">University Matcher</span>
                      <span class="ep-preview-agent-status status-done">Done</span>
                    </div>
                    <div class="ep-preview-agent-row">
                      <div class="ep-preview-agent-dot dot-blue ep-dot-pulse"></div>
                      <span class="ep-preview-agent-name">Scholarship Engine</span>
                      <span class="ep-preview-agent-status status-running">Active</span>
                    </div>
                    <div class="ep-preview-agent-row">
                      <div class="ep-preview-agent-dot dot-blue ep-dot-pulse"></div>
                      <span class="ep-preview-agent-name">Research Alignment</span>
                      <span class="ep-preview-agent-status status-running">Active</span>
                    </div>
                    <div class="ep-preview-agent-row">
                      <div class="ep-preview-agent-dot dot-gray"></div>
                      <span class="ep-preview-agent-name">SOP Generator</span>
                      <span class="ep-preview-agent-status status-waiting">Ready</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        """
    )


def render_problem_section() -> None:
    render_html(
        """
        <section class="ep-landing-section ep-section-alt" id="problem">
          <div class="ep-landing-section-center">
            <div class="ep-eyebrow">The Challenge</div>
            <h2 class="ep-section-heading">
              Studying abroad shouldn't feel like<br>a full-time research struggle.
            </h2>
            <p class="ep-section-subheading">
              Navigating global universities, scattered scholarships, faculty outreach, and complex eligibility criteria on your own is overwhelming.
            </p>
          </div>

          <div class="ep-problem-grid">
            <div class="ep-problem-card">
              <div class="ep-problem-icon">📚</div>
              <div class="ep-problem-title">Thousands of Programs</div>
              <div class="ep-problem-desc">Dozens of countries and thousands of universities — with no structured way to evaluate real profile fit.</div>
            </div>
            <div class="ep-problem-card">
              <div class="ep-problem-icon">💸</div>
              <div class="ep-problem-title">Scattered Scholarships</div>
              <div class="ep-problem-desc">Funding and fellowships are fragmented across obscure university pages, department sites, and portals.</div>
            </div>
            <div class="ep-problem-card">
              <div class="ep-problem-icon">❓</div>
              <div class="ep-problem-title">Opaque Eligibility</div>
              <div class="ep-problem-desc">Hard to know how your CGPA, test scores, and prerequisites stack up against actual admission standards.</div>
            </div>
            <div class="ep-problem-card">
              <div class="ep-problem-icon">🔬</div>
              <div class="ep-problem-title">Faculty Advisor Matching</div>
              <div class="ep-problem-desc">For graduate applicants, finding professors with active labs and open funding takes hundreds of manual hours.</div>
            </div>
            <div class="ep-problem-card">
              <div class="ep-problem-icon">✍️</div>
              <div class="ep-problem-title">Generic Statements of Purpose</div>
              <div class="ep-problem-desc">Most SOPs are generic and fail to weave academic background, research experience, and departmental fit together.</div>
            </div>
            <div class="ep-problem-card">
              <div class="ep-problem-icon">🗓️</div>
              <div class="ep-problem-title">No Coordinated Strategy</div>
              <div class="ep-problem-desc">Without strategic counseling, students miss critical deadlines and apply without a balanced Reach / Target / Safe portfolio.</div>
            </div>
          </div>

          <div class="ep-problem-resolution">
            <div class="ep-resolution-text">
              <strong>One intelligent workspace.</strong><br>
              A coordinated team of 9 AI agents doing the heavy lifting.
            </div>
          </div>
        </section>
        """
    )


def render_how_it_works() -> None:
    render_html(
        """
        <section class="ep-landing-section" id="how-it-works">
          <div class="ep-landing-section-center">
            <div class="ep-eyebrow">Seamless Process</div>
            <h2 class="ep-section-heading">How EduPath AI Works</h2>
            <p class="ep-section-subheading">
              Four structured steps from your raw academic background to a personalized admission roadmap.
            </p>
          </div>

          <div class="ep-steps-row">
            <div class="ep-step-card">
              <div class="ep-step-number">01</div>
              <div class="ep-step-icon">🧑‍🎓</div>
              <div class="ep-step-title">Build Your Profile</div>
              <div class="ep-step-desc">Input your CGPA, tests, target countries, degree level, research domain, and funding preferences in minutes.</div>
            </div>
            <div class="ep-step-connector">→</div>
            <div class="ep-step-card">
              <div class="ep-step-number">02</div>
              <div class="ep-step-icon">🤖</div>
              <div class="ep-step-title">AI Team Investigates</div>
              <div class="ep-step-desc">Specialized agents simultaneously analyze programs, verify minimum eligibility, locate funding, and match faculty labs.</div>
            </div>
            <div class="ep-step-connector">→</div>
            <div class="ep-step-card">
              <div class="ep-step-number">03</div>
              <div class="ep-step-icon">📊</div>
              <div class="ep-step-title">Review Recommendations</div>
              <div class="ep-step-desc">Get ranked opportunities categorized into Reach, Target, and Safe tiers with detailed dimensional score breakdowns.</div>
            </div>
            <div class="ep-step-connector">→</div>
            <div class="ep-step-card">
              <div class="ep-step-number">04</div>
              <div class="ep-step-icon">📝</div>
              <div class="ep-step-title">Generate Documents</div>
              <div class="ep-step-desc">Approve top choices to automatically draft grounded SOPs and targeted professor outreach emails tailored to each school.</div>
            </div>
          </div>
        </section>
        """
    )


def render_agents_section() -> None:
    render_html(
        """
        <section class="ep-landing-section ep-section-alt" id="agents">
          <div class="ep-landing-section-center">
            <div class="ep-eyebrow">The Multi-Agent Architecture</div>
            <h2 class="ep-section-heading">
              Not a chatbot.<br>
              <span class="ep-gradient-text">An entire counseling workforce.</span>
            </h2>
            <p class="ep-section-subheading">
              A central Supervisor Agent orchestrates 8 specialized AI agents — each dedicated to a distinct phase of your admission strategy.
            </p>
          </div>

          <div class="ep-agents-supervisor-row">
            <div class="ep-supervisor-big-card">
              <div class="ep-supervisor-icon">✦</div>
              <div class="ep-supervisor-info">
                <div class="ep-supervisor-name">Supervisor Agent (Orchestrator)</div>
                <div class="ep-supervisor-desc">Dynamically plans workflow execution, delegates tasks to domain specialists, merges verdicts, and coordinates human-in-the-loop decision checkpoints.</div>
              </div>
            </div>
          </div>

          <div class="ep-agents-grid">
            <div class="ep-agent-team-card">
              <div class="ep-agent-team-icon">👤</div>
              <div class="ep-agent-team-name">Profile Analyst</div>
              <div class="ep-agent-team-desc">Extracts academic strengths, publication records, coursework, and career goals into a structured applicant model.</div>
            </div>
            <div class="ep-agent-team-card">
              <div class="ep-agent-team-icon">🏫</div>
              <div class="ep-agent-team-name">University Matcher</div>
              <div class="ep-agent-team-desc">Discovers matching degree programs filtered by country, curriculum focus, ranking tier, and admission competitiveness.</div>
            </div>
            <div class="ep-agent-team-card">
              <div class="ep-agent-team-icon">💰</div>
              <div class="ep-agent-team-name">Scholarship Engine</div>
              <div class="ep-agent-team-desc">Surfaces graduate assistantships (RA/TA), merit fellowships, and government grants aligned with applicant nationality.</div>
            </div>
            <div class="ep-agent-team-card">
              <div class="ep-agent-team-icon">✅</div>
              <div class="ep-agent-team-name">Eligibility Verifier</div>
              <div class="ep-agent-team-desc">Strictly validates minimum GPA, standardized test scores (GRE/GMAT), and language test cutoffs for every opportunity.</div>
            </div>
            <div class="ep-agent-team-card">
              <div class="ep-agent-team-icon">🔬</div>
              <div class="ep-agent-team-name">Research Alignment</div>
              <div class="ep-agent-team-desc">Semantic matching of student research interests with faculty publications, ongoing lab grants, and thesis themes.</div>
            </div>
            <div class="ep-agent-team-card">
              <div class="ep-agent-team-icon">🔍</div>
              <div class="ep-agent-team-name">Source Verifier</div>
              <div class="ep-agent-team-desc">Checks official university portals to ensure deadlines, URLs, and application criteria are actively grounded.</div>
            </div>
            <div class="ep-agent-team-card">
              <div class="ep-agent-team-icon">⭐</div>
              <div class="ep-agent-team-name">Ranking Engine</div>
              <div class="ep-agent-team-desc">Executes deterministic multi-criteria scoring balancing research match, funding level, program tier, and deadlines.</div>
            </div>
            <div class="ep-agent-team-card">
              <div class="ep-agent-team-icon">📄</div>
              <div class="ep-agent-team-name">SOP Generator</div>
              <div class="ep-agent-team-desc">Drafts highly tailored statements of purpose grounded in your genuine experiences and target program specifics.</div>
            </div>
          </div>
        </section>
        """
    )


def render_personalization_section() -> None:
    render_html(
        """
        <section class="ep-landing-section" id="personalization">
          <div class="ep-landing-section-center">
            <div class="ep-eyebrow">Personalized Matching</div>
            <h2 class="ep-section-heading">Recommendations built for your exact profile.</h2>
            <p class="ep-section-subheading">
              Every score, tier, and rationale is computed from your actual qualifications — not generic marketing rankings.
            </p>
          </div>

          <div class="ep-personalization-demo">
            <div class="ep-demo-profile-card">
              <div class="ep-demo-card-label">Your Input Profile</div>
              <div class="ep-demo-profile-row"><span class="ep-demo-field">Undergrad CGPA</span><span class="ep-demo-val">3.78 / 4.0</span></div>
              <div class="ep-demo-profile-row"><span class="ep-demo-field">IELTS Academic</span><span class="ep-demo-val">7.5 Overall</span></div>
              <div class="ep-demo-profile-row"><span class="ep-demo-field">Research Focus</span><span class="ep-demo-val">AI Hardware & Edge Computing</span></div>
              <div class="ep-demo-profile-row"><span class="ep-demo-field">Publications</span><span class="ep-demo-val">1 IEEE Workshop Paper</span></div>
              <div class="ep-demo-profile-row"><span class="ep-demo-field">Funding Target</span><span class="ep-demo-val">100% Fully Funded (RA/TA)</span></div>
              <div class="ep-demo-profile-row"><span class="ep-demo-field">Target Countries</span><span class="ep-demo-val">USA, Canada, Germany</span></div>
            </div>

            <div class="ep-demo-arrow">→</div>

            <div class="ep-demo-result-card">
              <div class="ep-demo-card-label">AI Strategy Output</div>
              <div class="ep-demo-fit-row">
                <span class="ep-demo-fit-label">Research Fit</span>
                <div class="ep-demo-fit-bar-track"><div class="ep-demo-fit-bar" style="width:95%"></div></div>
                <span class="ep-demo-fit-score">95%</span>
              </div>
              <div class="ep-demo-fit-row">
                <span class="ep-demo-fit-label">Funding Fit</span>
                <div class="ep-demo-fit-bar-track"><div class="ep-demo-fit-bar" style="width:90%"></div></div>
                <span class="ep-demo-fit-score">90%</span>
              </div>
              <div class="ep-demo-fit-row">
                <span class="ep-demo-fit-label">Academic Fit</span>
                <div class="ep-demo-fit-bar-track"><div class="ep-demo-fit-bar" style="width:88%"></div></div>
                <span class="ep-demo-fit-score">88%</span>
              </div>
              <div class="ep-demo-direction">
                <div class="ep-demo-direction-label">Optimized Strategy Tier</div>
                <div class="ep-demo-direction-value">Reach: CMU CyLab · Target: Purdue ECE · Safe: TU Munich</div>
              </div>
              <div class="ep-demo-matches">
                <span class="ep-badge indigo">Prof. Dawn Song Aligned</span>
                <span class="ep-badge success">Full Tuition + $36k Stipend</span>
                <span class="ep-badge purple">Priority Fall 2027</span>
              </div>
            </div>
          </div>
        </section>
        """
    )


def render_features_section() -> None:
    render_html(
        """
        <section class="ep-landing-section ep-section-alt" id="features">
          <div class="ep-landing-section-center">
            <div class="ep-eyebrow">Comprehensive Suite</div>
            <h2 class="ep-section-heading">Everything in one unified workspace.</h2>
            <p class="ep-section-subheading">
              From exploratory search to submitting polished applications, EduPath AI handles every phase.
            </p>
          </div>

          <div class="ep-features-grid">
            <div class="ep-feature-card">
              <div class="ep-feature-icon">🏫</div>
              <div class="ep-feature-title">Program Discovery</div>
              <div class="ep-feature-desc">Search thousands of graduate and undergraduate programs with multi-dimensional filtering for tuition, deadlines, and requirements.</div>
            </div>
            <div class="ep-feature-card">
              <div class="ep-feature-icon">💰</div>
              <div class="ep-feature-title">Funding & Scholarships</div>
              <div class="ep-feature-desc">Uncover hidden fellowships, departmental assistantships, and international scholarships tailored to your citizenship.</div>
            </div>
            <div class="ep-feature-card">
              <div class="ep-feature-icon">👨‍🏫</div>
              <div class="ep-feature-title">Professor Matching</div>
              <div class="ep-feature-desc">Match your research interests with active faculty advisors and generate personalized cold email drafts for advisor outreach.</div>
            </div>
            <div class="ep-feature-card">
              <div class="ep-feature-icon">📋</div>
              <div class="ep-feature-title">Application Tracker</div>
              <div class="ep-feature-desc">Track application milestones across Saved, Preparing, Applied, Interview, and Accepted stages in a clean Kanban board.</div>
            </div>
            <div class="ep-feature-card">
              <div class="ep-feature-icon">📝</div>
              <div class="ep-feature-title">Document Workspace</div>
              <div class="ep-feature-desc">Generate, iterate, and export version-controlled Statements of Purpose grounded in your uploaded transcripts and CV.</div>
            </div>
            <div class="ep-feature-card">
              <div class="ep-feature-icon">🧠</div>
              <div class="ep-feature-title">Cross-Session AI Memory</div>
              <div class="ep-feature-desc">EduPath AI remembers your past searches, preferences, and feedback across sessions to continually refine its recommendations.</div>
            </div>
          </div>
        </section>
        """
    )


def render_trust_section() -> None:
    render_html(
        """
        <section class="ep-landing-section" id="trust">
          <div class="ep-landing-section-center">
            <div class="ep-eyebrow">Trust & Transparency</div>
            <h2 class="ep-section-heading">Built for high-stakes academic decisions.</h2>
            <p class="ep-section-subheading">
              EduPath AI grounds every recommendation in verifiable institutional data with direct links back to official sources.
            </p>
          </div>

          <div class="ep-trust-grid">
            <div class="ep-trust-card">
              <div class="ep-trust-icon">🏛️</div>
              <div class="ep-trust-title">University Portals</div>
              <div class="ep-trust-desc">Program data and admission cutoffs sourced directly from official department and university catalog pages.</div>
            </div>
            <div class="ep-trust-card">
              <div class="ep-trust-icon">📜</div>
              <div class="ep-trust-title">Scholarship Foundations</div>
              <div class="ep-trust-desc">Funding opportunities linked to verifiable government, endowment, and university fellowship portals.</div>
            </div>
            <div class="ep-trust-card">
              <div class="ep-trust-icon">👨‍🔬</div>
              <div class="ep-trust-title">Faculty Directories</div>
              <div class="ep-trust-desc">Advisor matches linked to authentic lab websites, publication records, and university department rosters.</div>
            </div>
            <div class="ep-trust-card">
              <div class="ep-trust-icon">📊</div>
              <div class="ep-trust-title">Recognized Rankings</div>
              <div class="ep-trust-desc">Contextual university tiering benchmarked against QS, THE, and global subject rankings.</div>
            </div>
          </div>

          <div class="ep-trust-disclaimer">
            <div class="ep-disclaimer-icon">⚠️</div>
            <div class="ep-disclaimer-text">
              <strong>Official Verification Note:</strong> Always verify application deadlines, tuition rates, and prerequisite coursework directly on official university portals prior to submitting formal applications. EduPath AI provides AI research assistance.
            </div>
          </div>
        </section>
        """
    )


def render_cta_section() -> None:
    render_html(
        """
        <section class="ep-cta-section">
          <div class="ep-cta-inner">
            <div class="ep-eyebrow" style="color: #A5B4FC; margin-bottom: 0.5rem;">✦ START YOUR JOURNEY</div>
            <h2 class="ep-cta-heading">Your next academic opportunity is out there.</h2>
            <p class="ep-cta-sub">Let your dedicated AI counseling workforce find the perfect path to it today.</p>
            <a href="?page=login" class="ep-btn-cta">Start Free AI Counseling →</a>
          </div>
        </section>
        """
    )


def render_footer() -> None:
    render_html(
        """
        <footer class="ep-landing-footer">
          <div class="ep-footer-inner">
            <div class="ep-footer-brand">
              <div class="ep-footer-logo">E</div>
              <div style="text-align: left;">
                <div class="ep-footer-brand-name">EduPath AI</div>
                <div class="ep-footer-tagline">AI-powered study abroad counseling.</div>
              </div>
            </div>
            <div class="ep-footer-links">
              <a href="#how-it-works" class="ep-footer-link">How It Works</a>
              <a href="#agents" class="ep-footer-link">AI Agents</a>
              <a href="#features" class="ep-footer-link">Features</a>
              <a href="#trust" class="ep-footer-link">Trust & Sources</a>
              <a href="?page=login" class="ep-footer-link">Sign In</a>
            </div>
            <div class="ep-footer-copy">© 2026 EduPath AI. Grounded in real university data. All rights reserved.</div>
          </div>
        </footer>
        """
    )


def main() -> None:
    _hide_streamlit_chrome()
    render_navigation()
    render_hero()
    render_problem_section()
    render_how_it_works()
    render_agents_section()
    render_personalization_section()
    render_features_section()
    render_trust_section()
    render_cta_section()
    render_footer()


main()
