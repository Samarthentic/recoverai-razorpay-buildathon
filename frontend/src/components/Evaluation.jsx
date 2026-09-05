import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Sparkles, 
  ShieldCheck, 
  TrendingUp, 
  Target, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Layers, 
  Info,
  RefreshCw,
  Award,
  BarChart3
} from 'lucide-react';
import { getDashboardStats } from '../api/client';
import { formatINR, formatINRLakh, formatPercent } from '../utils/formatters';

export default function Evaluation() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error('Error fetching evaluation benchmark stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center min-h-[440px]">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-7 w-7 text-indigo-600 animate-spin" />
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Loading Benchmark Evaluation Metrics...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Benchmark Notice */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-indigo-600" />
              <h1 className="text-lg font-bold text-slate-950">Synthetic Ground-Truth Benchmark Console</h1>
              <span className="px-2.5 py-0.5 rounded text-[10px] font-extrabold bg-purple-100 text-purple-900 border border-purple-200 uppercase">
                Dual-Track Evaluation
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-3xl">
              Unlike unscientific systems that measure recovery against what an AI itself predicts, RecoverAI measures financial and classification accuracy against an independent, hidden synthetic ground-truth benchmark.
            </p>
          </div>

          <button
            onClick={fetchStats}
            className="p-2 border border-slate-200 hover:bg-slate-50 rounded-lg text-slate-600 transition self-start md:self-auto"
            title="Refresh benchmark data"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        {/* Disclaimer Callout */}
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 text-xs flex items-start gap-2.5">
          <Info className="h-4 w-4 text-indigo-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-900">Synthetic Benchmark Notice:</span> All payment characteristics, customer behavior profiles, and recovery outcomes are generated via deterministic SHA-256 PRNG physics. No real banking movement occurs.
          </div>
        </div>
      </div>

      {/* SECTION 1: FINANCIAL REVENUE BENCHMARKS */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-600" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              1. Financial Revenue Recovery Benchmark
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">Sample: {stats.total_payments} Ingested Payments</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Total Revenue at Risk
            </span>
            <span className="text-2xl font-black text-slate-950 font-numeric block pt-0.5">
              {formatINRLakh(stats.total_at_risk)}
            </span>
            <span className="text-[10px] text-slate-400 mt-1 block">
              Gross failed volume
            </span>
          </div>

          <div className="p-4 rounded-lg bg-indigo-50/60 border border-indigo-200 space-y-1">
            <span className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider block">
              Ground-Truth Recoverable
            </span>
            <span className="text-2xl font-black text-indigo-950 font-numeric block pt-0.5">
              {formatINRLakh(stats.ground_truth_recoverable_revenue)}
            </span>
            <span className="text-[10px] text-indigo-700 mt-1 block">
              Realistic synthetic target pool
            </span>
          </div>

          <div className="p-4 rounded-lg bg-purple-50/60 border border-purple-200 space-y-1">
            <span className="text-[10px] font-bold text-purple-700 uppercase tracking-wider block">
              AI Predicted Recoverable
            </span>
            <span className="text-2xl font-black text-purple-950 font-numeric block pt-0.5">
              {formatINRLakh(stats.ai_predicted_recoverable_revenue)}
            </span>
            <span className="text-[10px] text-purple-700 mt-1 block">
              Flagged recoverable by AI
            </span>
          </div>

          <div className="p-4 rounded-lg bg-emerald-50/60 border border-emerald-200 space-y-1">
            <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
              Simulated Revenue Recovered
            </span>
            <span className="text-2xl font-black text-emerald-700 font-numeric block pt-0.5">
              {formatINRLakh(stats.total_recovered)}
            </span>
            <span className="text-[10px] text-emerald-800 mt-1 block">
              Measured in simulations
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-4 rounded-lg bg-slate-900 text-white flex items-center justify-between border border-slate-800">
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Recovery Efficiency (Against Ground-Truth Target)
              </span>
              <div className="text-2xl font-black text-emerald-400 font-numeric mt-0.5">
                {formatPercent(stats.recovery_efficiency)}
              </div>
              <p className="text-[10px] text-slate-400 mt-0.5">
                Formula: Recovered Revenue / Ground-Truth Recoverable Pool
              </p>
            </div>
            <Award className="h-8 w-8 text-emerald-400 opacity-80" />
          </div>

          <div className="p-4 rounded-lg bg-slate-900 text-white flex items-center justify-between border border-slate-800">
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Gross Recovery Rate
              </span>
              <div className="text-2xl font-black text-indigo-400 font-numeric mt-0.5">
                {formatPercent(stats.recovery_rate)}
              </div>
              <p className="text-[10px] text-slate-400 mt-0.5">
                Formula: Recovered Revenue / Total Revenue at Risk
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-indigo-400 opacity-80" />
          </div>
        </div>
      </div>

      {/* DUAL EVALUATION TRACK: GEMINI LLM VS FULL PIPELINE */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SECTION 2: GEMINI LLM ISOLATED METRICS */}
        <div className="bg-slate-900 text-white rounded-xl border border-slate-800 shadow-2xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-indigo-400" />
              <h2 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
                2. Gemini LLM Metrics
              </h2>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
              gemini-3.5-flash
            </span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed font-medium">
            Calculated <span className="text-white font-bold">strictly over records generated by Gemini</span> (excludes heuristic fallback & pre-screens).
          </p>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700">
              <span className="text-slate-400 block font-bold text-[10px] uppercase">LLM Analyzed Volume</span>
              <span className="text-xl font-bold text-white mt-1 block font-numeric">
                {stats.llm_analyzed_count || 0}
              </span>
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                Fallback Used: {stats.heuristic_fallback_count || 0}
              </span>
            </div>

            <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700">
              <span className="text-slate-400 block font-bold text-[10px] uppercase">AI Recoverability F1</span>
              <span className="text-xl font-bold text-emerald-400 mt-1 block font-numeric">
                {formatPercent(stats.llm_f1)}
              </span>
              <span className="text-[10px] text-slate-400 mt-0.5 block">Harmonic Mean</span>
            </div>

            <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700">
              <span className="text-slate-400 block font-bold text-[10px] uppercase">AI Precision</span>
              <span className="text-xl font-bold text-indigo-400 mt-1 block font-numeric">
                {formatPercent(stats.llm_precision)}
              </span>
              <span className="text-[10px] text-slate-400 mt-0.5 block">TP / (TP + FP)</span>
            </div>

            <div className="bg-slate-800/80 p-3.5 rounded-lg border border-slate-700">
              <span className="text-slate-400 block font-bold text-[10px] uppercase">AI Recall</span>
              <span className="text-xl font-bold text-indigo-400 mt-1 block font-numeric">
                {formatPercent(stats.llm_recall)}
              </span>
              <span className="text-[10px] text-slate-400 mt-0.5 block">TP / (TP + FN)</span>
            </div>

            <div className="col-span-2 bg-slate-800/80 p-3.5 rounded-lg border border-slate-700 flex items-center justify-between">
              <div>
                <span className="text-slate-400 block font-bold text-[10px] uppercase">Intervention Match Accuracy</span>
                <span className="text-lg font-bold text-purple-400 mt-0.5 block font-numeric">
                  {formatPercent(stats.llm_intervention_accuracy)}
                </span>
                <span className="text-[10px] text-slate-400">Exact match with GT optimal action</span>
              </div>
              <Target className="h-6 w-6 text-purple-400 opacity-60" />
            </div>
          </div>
        </div>

        {/* SECTION 3: FULL PIPELINE METRICS */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-600" />
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                3. Full Pipeline Metrics
              </h2>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
              Total ({stats.total_payments})
            </span>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed font-medium">
            Calculated across <span className="font-bold text-slate-900">all 520 records</span> (Gemini + Pre-screening + Heuristic Fallback).
          </p>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-bold text-[10px] uppercase">Pipeline F1 Score</span>
              <span className="text-xl font-bold text-slate-950 mt-1 block font-numeric">
                {formatPercent(stats.ai_f1)}
              </span>
              <span className="text-[10px] text-slate-400 mt-0.5 block">Composite classification</span>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-bold text-[10px] uppercase">Intervention Accuracy</span>
              <span className="text-xl font-bold text-slate-950 mt-1 block font-numeric">
                {formatPercent(stats.intervention_accuracy)}
              </span>
              <span className="text-[10px] text-slate-400 mt-0.5 block">Best action match</span>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-bold text-[10px] uppercase">Pipeline Precision</span>
              <span className="text-lg font-bold text-slate-800 mt-1 block font-numeric">
                {formatPercent(stats.ai_precision)}
              </span>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 block font-bold text-[10px] uppercase">Pipeline Recall</span>
              <span className="text-lg font-bold text-slate-800 mt-1 block font-numeric">
                {formatPercent(stats.ai_recall)}
              </span>
            </div>

            <div className="col-span-2 p-3.5 rounded-lg bg-emerald-50/70 border border-emerald-200 flex items-center justify-between">
              <div>
                <span className="text-emerald-800 block font-bold text-[10px] uppercase">Approved Action Success Rate</span>
                <span className="text-lg font-bold text-emerald-950 mt-0.5 block font-numeric">
                  {formatPercent(stats.approved_action_success_rate)}
                </span>
                <span className="text-[10px] text-emerald-800">Conversion percentage of policy-cleared actions</span>
              </div>
              <ShieldCheck className="h-6 w-6 text-emerald-600 opacity-80" />
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 4: POLICY IMPACT & SAFETY GOVERNANCE */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <ShieldCheck className="h-4 w-4 text-indigo-600" />
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            4. Deterministic Governance & Stopping Rules Impact
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-500 font-bold block uppercase text-[10px]">Actions Approved</span>
            <div className="flex items-baseline gap-1.5 pt-0.5">
              <span className="text-2xl font-black text-emerald-600 font-numeric">{stats.approved_count || 0}</span>
              <span className="text-slate-400 font-medium">cases</span>
            </div>
            <p className="text-[11px] text-slate-500 pt-1">
              Cleared all 8 deterministic safety invariants.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-rose-50/70 border border-rose-200 space-y-1">
            <span className="text-rose-800 font-bold block uppercase text-[10px]">Actions Blocked</span>
            <div className="flex items-baseline gap-1.5 pt-0.5">
              <span className="text-2xl font-black text-rose-600 font-numeric">{stats.blocked_count || 0}</span>
              <span className="text-rose-800 font-bold">({formatPercent(stats.policy_block_rate)})</span>
            </div>
            <p className="text-[11px] text-rose-800 pt-1">
              Prevented unnecessary customer friction and fee waste.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-amber-50/70 border border-amber-200 space-y-1">
            <span className="text-amber-900 font-bold block uppercase text-[10px]">Escalated to Human</span>
            <div className="flex items-baseline gap-1.5 pt-0.5">
              <span className="text-2xl font-black text-amber-600 font-numeric">{stats.escalated_count || 0}</span>
              <span className="text-amber-900 font-bold">({formatPercent(stats.escalation_rate)})</span>
            </div>
            <p className="text-[11px] text-amber-900 pt-1">
              Held for manual operator review in console.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
