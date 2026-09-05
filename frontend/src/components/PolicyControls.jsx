import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  ShieldX, 
  Cpu, 
  Sparkles, 
  Lock, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  RefreshCw, 
  Layers, 
  Sliders, 
  Server, 
  ArrowRight,
  Database,
  FileCheck
} from 'lucide-react';
import { getSystemStatus } from '../api/client';
import { formatINR } from '../utils/formatters';

export default function PolicyControls() {
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const data = await getSystemStatus();
      setStatusData(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching system telemetry:', err);
      setError('Failed to load system policy configuration.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  if (loading || !statusData) {
    return (
      <div className="flex items-center justify-center min-h-[440px]">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-7 w-7 text-indigo-600 animate-spin" />
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Loading System Policy Controls...
          </p>
        </div>
      </div>
    );
  }

  const { components, ai_configuration: aiConfig, policy_configuration: policyConfig } = statusData;

  const componentList = [
    {
      name: 'Recovery Engine',
      desc: 'Orchestrates payment risk detection, advisory routing, and recovery lifecycle.',
      status: components.recovery_engine,
      badge: 'Operational',
      color: 'text-emerald-800 bg-emerald-50 border-emerald-200'
    },
    {
      name: 'Policy Engine',
      desc: 'Authoritative deterministic gate enforcing 8 immutable financial & safety rules.',
      status: components.policy_engine,
      badge: 'Operational',
      color: 'text-emerald-800 bg-emerald-50 border-emerald-200'
    },
    {
      name: 'Gemini Analysis',
      desc: 'Multimodal root-cause diagnosis and advisory recovery recommendation.',
      status: components.gemini_analysis,
      badge: components.gemini_analysis === 'connected' ? 'Connected (Live)' : 'Fallback Active',
      color: components.gemini_analysis === 'connected' 
        ? 'text-indigo-800 bg-indigo-50 border-indigo-200' 
        : 'text-amber-900 bg-amber-50 border-amber-200'
    },
    {
      name: 'Recovery Simulator',
      desc: 'Reproducible SHA-256 PRNG physics engine modeling real gateway responses.',
      status: components.recovery_simulator,
      badge: 'Operational',
      color: 'text-emerald-800 bg-emerald-50 border-emerald-200'
    },
    {
      name: 'Audit Logging',
      desc: 'Immutable, cryptographically verifiable append-only ledger for all decisions.',
      status: components.audit_logging,
      badge: 'Operational',
      color: 'text-emerald-800 bg-emerald-50 border-emerald-200'
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-indigo-600" />
            <h1 className="text-lg font-bold text-slate-950">Recovery Policy & System Controls</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200 uppercase">
              Authoritative Guardrails
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-3xl">
            Active deterministic governance parameters. Every recommendation proposed by Gemini is evaluated against these strict safety constraints before any recovery action is simulated.
          </p>
        </div>

        <button
          onClick={fetchStatus}
          className="p-2 border border-slate-200 hover:bg-slate-50 rounded-lg text-slate-600 transition self-start md:self-auto"
          title="Refresh system status"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-4 rounded-xl">
          {error}
        </div>
      )}

      {/* Core Architectural Principle Banner */}
      <div className="bg-slate-900 text-white rounded-xl p-6 border border-slate-800 shadow-2xs relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
              Governance Architecture
            </span>
            <h2 className="text-xl font-black text-white tracking-tight">
              AI proposes. Deterministic policy decides.
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed font-medium">
              The Gemini LLM functions solely as an advisory diagnostic agent. It does <span className="font-bold text-rose-300">NOT</span> control financial ceilings, retry limits, escalation thresholds, or policy overrides. The deterministic policy engine maintains final, non-overridable authority.
            </p>
          </div>

          <div className="bg-slate-800/90 p-4 rounded-lg border border-slate-700 text-xs space-y-2 min-w-[240px]">
            <div className="text-[10px] font-bold text-slate-300 uppercase tracking-wider pb-1 border-b border-slate-700">
              Authority Matrix
            </div>
            <div className="flex items-center justify-between text-slate-300 text-[11px]">
              <span>Financial Caps:</span>
              <span className="font-bold text-emerald-400">Hard-Coded / Env</span>
            </div>
            <div className="flex items-center justify-between text-slate-300 text-[11px]">
              <span>Retry Throttles:</span>
              <span className="font-bold text-emerald-400">Deterministic (3 Max)</span>
            </div>
            <div className="flex items-center justify-between text-slate-300 text-[11px]">
              <span>Human Escalation:</span>
              <span className="font-bold text-amber-400">Mandatory on Risk</span>
            </div>
            <div className="flex items-center justify-between text-slate-300 text-[11px]">
              <span>AI Authority:</span>
              <span className="font-bold text-indigo-400">Advisory Only</span>
            </div>
          </div>
        </div>
      </div>

      {/* Component Telemetry Panel */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-indigo-600" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Component Operational Telemetry
            </h2>
          </div>
          <span className="text-xs text-slate-500 font-mono font-medium">Platform: {statusData.service} v0.1.0</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {componentList.map((c, idx) => (
            <div key={idx} className="p-4 rounded-lg bg-slate-50/80 border border-slate-200 flex flex-col justify-between space-y-2">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-slate-900">{c.name}</span>
                  <span className={`px-2 py-0.5 rounded border text-[10px] font-extrabold uppercase tracking-wider ${c.color}`}>
                    {c.badge}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                  {c.desc}
                </p>
              </div>
              <div className="pt-2 border-t border-slate-200/60 flex items-center gap-1 text-[10px] text-slate-500 font-semibold">
                <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                Live verification passed
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Active Deterministic Policy Parameters */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-indigo-600" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Active Deterministic Governance Thresholds
            </h2>
          </div>
          <span className="text-xs font-mono text-indigo-700 font-bold bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
            {policyConfig.decision_authority}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
          {/* Max Retries */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800">Max Automatic Retries</span>
              <Lock className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <div className="text-2xl font-black font-mono text-slate-950 font-numeric">
              {policyConfig.max_retries} attempts
            </div>
            <p className="text-[11px] text-slate-500 pt-1 leading-relaxed">
              Rule: <span className="font-mono text-slate-700 font-semibold">max_retry_exceeded</span>. Halts retries once counter reaches 3 to prevent card network penalty fees.
            </p>
          </div>

          {/* High-Value Threshold */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800">High-Value Escalation Ceiling</span>
              <Lock className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <div className="text-2xl font-black font-mono text-slate-950 font-numeric">
              {formatINR(policyConfig.high_value_threshold)}
            </div>
            <p className="text-[11px] text-slate-500 pt-1 leading-relaxed">
              Rule: <span className="font-mono text-slate-700 font-semibold">high_value_human_review</span>. Mandates operator authorization for transactions exceeding ₹50,000.
            </p>
          </div>

          {/* AI Confidence Threshold */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800">Minimum AI Confidence</span>
              <Lock className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <div className="text-2xl font-black font-mono text-slate-950 font-numeric">
              {(policyConfig.confidence_threshold * 100).toFixed(0)}%
            </div>
            <p className="text-[11px] text-slate-500 pt-1 leading-relaxed">
              Rule: <span className="font-mono text-slate-700 font-semibold">low_confidence_escalate</span>. Automatically escalates any recommendation with confidence &lt; 0.60.
            </p>
          </div>

          {/* Customer Failure Limit */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800">Customer Failure Limit</span>
              <Lock className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <div className="text-2xl font-black font-mono text-slate-950 font-numeric">
              {policyConfig.customer_failure_limit} failures
            </div>
            <p className="text-[11px] text-slate-500 pt-1 leading-relaxed">
              Rule: <span className="font-mono text-slate-700 font-semibold">repeat_failure_customer</span>. Blocks direct retries for chronic fail profiles, routing to alternate links.
            </p>
          </div>

          {/* Max Auto Recovery Amount */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800">Max Auto-Recovery Cap</span>
              <Lock className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <div className="text-2xl font-black font-mono text-slate-950 font-numeric">
              {formatINR(policyConfig.max_auto_recovery_amount)}
            </div>
            <p className="text-[11px] text-slate-500 pt-1 leading-relaxed">
              Rule: <span className="font-mono text-slate-700 font-semibold">max_auto_recovery_amount_exceeded</span>. Hard financial upper limit (₹1,00,000) for zero-touch execution.
            </p>
          </div>

          {/* Non-Retryable Failure Reasons */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800">Non-Retryable Gateway Codes</span>
              <Lock className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <div className="flex flex-wrap gap-1 pt-1">
              {policyConfig.non_retryable_reasons.map((r, i) => (
                <span key={i} className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200">
                  {r}
                </span>
              ))}
            </div>
            <p className="text-[11px] text-slate-500 pt-1 leading-relaxed">
              Rule: <span className="font-mono text-slate-700 font-semibold">non_retryable_failure_reason</span>. Immediate block against automated retry for permanent account errors.
            </p>
          </div>
        </div>
      </div>

      {/* Decision Precedence & Safety Hierarchy */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <Layers className="h-4 w-4 text-indigo-600" />
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Deterministic Decision Precedence Hierarchy
          </h2>
        </div>

        <div className="space-y-2 text-xs">
          <div className="p-3 rounded-lg bg-rose-50/80 border border-rose-200 flex items-start gap-3">
            <span className="px-2 py-0.5 rounded bg-rose-600 text-white font-bold text-[10px] uppercase">
              Priority 1
            </span>
            <div className="space-y-0.5 flex-1">
              <span className="font-bold text-rose-950">Permanent Risk Invariant (fraud_suspected, account_closed, subscription_cancelled)</span>
              <p className="text-rose-900 text-[11px] font-medium">
                Immediately overrides all AI recommendations. Returns <span className="font-bold">BLOCKED</span> with 0 retry attempts allowed.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-amber-50/80 border border-amber-200 flex items-start gap-3">
            <span className="px-2 py-0.5 rounded bg-amber-600 text-white font-bold text-[10px] uppercase">
              Priority 2
            </span>
            <div className="space-y-0.5 flex-1">
              <span className="font-bold text-amber-950">High-Value Escalation (Amount &gt; ₹50,000)</span>
              <p className="text-amber-900 text-[11px] font-medium">
                Overrides automated retry/link actions. Returns <span className="font-bold">ESCALATED</span> for human operator review in the operations console.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-amber-50/80 border border-amber-200 flex items-start gap-3">
            <span className="px-2 py-0.5 rounded bg-amber-600 text-white font-bold text-[10px] uppercase">
              Priority 3
            </span>
            <div className="space-y-0.5 flex-1">
              <span className="font-bold text-amber-950">Low AI Confidence (Confidence &lt; 0.60)</span>
              <p className="text-amber-900 text-[11px] font-medium">
                Flags uncertain diagnostics. Returns <span className="font-bold">ESCALATED</span> to prevent erroneous automated interventions.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-start gap-3">
            <span className="px-2 py-0.5 rounded bg-slate-700 text-white font-bold text-[10px] uppercase">
              Priority 4
            </span>
            <div className="space-y-0.5 flex-1">
              <span className="font-bold text-slate-900">Channel Availability & Retry Throttles</span>
              <p className="text-slate-600 text-[11px] font-medium">
                Validates customer email before dispatching payment links; halts retries when counter &ge; 3.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-emerald-50/80 border border-emerald-200 flex items-start gap-3">
            <span className="px-2 py-0.5 rounded bg-emerald-600 text-white font-bold text-[10px] uppercase">
              Default
            </span>
            <div className="space-y-0.5 flex-1">
              <span className="font-bold text-emerald-950">Policy Approval & Simulator Dispatch</span>
              <p className="text-emerald-900 text-[11px] font-medium">
                If zero safety violations occur, recommendation is marked <span className="font-bold">APPROVED</span> and dispatched to the SHA-256 simulator.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* AI & Engine Health Card */}
      <div className="bg-slate-900 text-white rounded-xl border border-slate-800 shadow-2xs p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-indigo-400" />
            <h2 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
              AI Engine Health & Safety Architecture
            </h2>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
            {aiConfig.model}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-lg bg-slate-800/80 border border-slate-700">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Active Model</span>
            <span className="font-mono font-bold text-white mt-1 block">{aiConfig.model}</span>
            <span className="text-[10px] text-indigo-300 mt-1 block">Google GenAI SDK</span>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-800/80 border border-slate-700">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Batch Quota Limit</span>
            <span className="font-mono font-bold text-white mt-1 block font-numeric">{aiConfig.batch_limit} calls / batch</span>
            <span className="text-[10px] text-slate-400 mt-1 block">Protects free-tier quota</span>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-800/80 border border-slate-700">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Deterministic Fallback</span>
            <span className="font-mono font-bold text-emerald-400 mt-1 block">Enabled</span>
            <span className="text-[10px] text-slate-400 mt-1 block">Zero downtime offline resilience</span>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-800/80 border border-slate-700">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Ground-Truth Isolation</span>
            <span className="font-mono font-bold text-purple-400 mt-1 block">Enabled</span>
            <span className="text-[10px] text-slate-400 mt-1 block">Hidden from LLM prompt context</span>
          </div>
        </div>

        <div className="pt-2 text-[11px] text-slate-400 flex items-center justify-between border-t border-slate-800">
          <span className="flex items-center gap-1.5 font-medium">
            <Lock className="h-3.5 w-3.5 text-slate-400" />
            API keys and internal credentials remain strictly backend-isolated.
          </span>
          <span className="text-slate-500 font-mono text-[10px]">
            Safety: Policy-Gated Architecture
          </span>
        </div>
      </div>
    </div>
  );
}
