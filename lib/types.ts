// lib/types.ts

export interface JDUnderstanding {
  role_title: string;
  seniority_level: string;
  domain: string;
  required_skills: string[];
  nice_to_have_skills: string[];
  key_responsibilities: string[];
  required_years_experience: string;
  soft_skills: string[];
  hidden_expectations: string[];
}

export interface CVBullet {
  role: string;
  company: string;
  text: string;
}

export interface CVUnderstanding {
  candidate_name: string;
  headline: string;
  total_years_experience: string;
  current_role: string;
  career_trajectory: string;
  domain_expertise: string[];
  core_strengths: string[];
  technical_skills: string[];
  soft_skills: string[];
  notable_achievements: string[];
  education: string[];
  bullets: CVBullet[];
  red_flag_signals: string[];
}

export interface ContentIssue {
  issue_type: "weak_bullet" | "no_metrics" | "vague_claim" | "buzzword_spam";
  original: string;
  problem: string;
  improved_version: string;
}

export interface SkillGaps {
  critical_missing: string[];
  secondary_missing: string[];
  transferable: string[];
}

export interface PositioningIssue {
  problem: string;
  rewritten_summary: string;
}

export interface RedFlag {
  flag: string;
  risk_explanation: string;
}

export interface Improvements {
  content_issues: ContentIssue[];
  skill_gaps: SkillGaps;
  positioning_issues: PositioningIssue[];
  experience_issues: string[];
  formatting_issues: string[];
  red_flags: RedFlag[];
}

export interface Suggestions {
  micro_fixes: string[];
  macro_fixes: string[];
  strategic_advice: string[];
}

export interface HiringDecision {
  recommendation: "Hire" | "Consider" | "Reject";
  reason: string;
  top_risks: string[];
}

export interface DimensionScores {
  jd_match: number;
  cv_quality: number;
  experience_depth: number;
  formatting: number;
  risk: number;
}

export interface Evaluation {
  overall_score: number;
  grade: "Strong Hire" | "Good Fit" | "Moderate" | "Weak";
  confidence: number;
  summary: string;
  dimension_scores: DimensionScores;
  strengths: string[];
  weaknesses: string[];
  improvements: Improvements;
  suggestions: Suggestions;
  hiring_decision: HiringDecision;
}

export interface ScreeningResult {
  jd_understanding: JDUnderstanding;
  cv_understanding: CVUnderstanding;
  evaluation: Evaluation;
}

// SSE progress events streamed from the API
export type ProgressEvent =
  | { type: "progress"; message: string }
  | { type: "result"; data: ScreeningResult }
  | { type: "error"; message: string };
