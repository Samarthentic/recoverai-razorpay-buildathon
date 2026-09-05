import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  TrendingUp, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Sparkles, 
  Database, 
  Play, 
  ArrowRight, 
  Layers, 
  Cpu, 
  ArrowUpRight,
  RefreshCw,
  Info,
  ShieldCheck,
  Zap,
  Target
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { 
  getDashboardStats, 
  runBatch, 
  seedPayments, 
  getDemoCases,
  getBatchResults 
} from '../api/client';
import { 
  formatINR, 
  formatINRLakh, 
  formatPercent, 
  formatPercentCompact,
  getDecisionBadge, 
  getMethodBadge,
  getActionBadge 
} from '../utils/formatters';

export default function Dashboard({ onSelectPayment, onViewPayments, onViewEvaluation, onViewAudit, onViewPolicy }) {
  const [stats, setStats] = useState(null);
  const [demoCases, setDemoCases] = useState([]);
  const [recentResults, setRecentResults] = useState([]);
  const [isBatchRunning, setIsBatchRunning] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [batchCompletedMsg, setBatchCompletedMsg] = useState(null);

  const fetchData = async () => {
    try {
      const [statsData, demoData] = await Promise.all([
        getDashboardStats(),
        getDemoCases().catch(() => [])
      ]);
      setStats(statsData);
      setDemoCases(demoData || []);

      if (statsData?.batch_id) {
        const results = await getBatchResults(statsData.batch_id, { limit: 8 });
        setRecentResults(results || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard telemetry:', error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeedData = async () => {
    setIsSeeding(true);
    setBatchCompletedMsg(null);
    try {
      await seedPayments();
      await fetchData();
    } catch (error) {
      console.error('Error seeding data:', error);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleRunBatch = async () => {
    setIsBatchRunning(true);
    setBatchCompletedMsg(null);
    try {
      const batchRes = await runBatch();
      await fetchData();
      setBatchCompletedMsg(`Batch ${batchRes.id.slice(0, 12)} completed: ${batchRes.total_payments} payments analyzed.`);
      setTimeout(() => setBatchCompletedMsg(null), 6000);
    } catch (error) {
      console.error('Error executing batch:', error);
    } finally {
      setIsBatchRunning(false);
    }
  };

  if (!stats) {
    return (
      <div className="flex items-center justify-center min-h-[440px]">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-7 w-7 text-indigo-600 animate-spin" />
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Loading Operations Telemetry...
          </p>
        </div>
      </div>
    );
  }

  const policyChartData = [
    { name: 'Approved', count: stats.approved_count || 0, color: '#10b981' },
    { name: 'Blocked', count: stats.blocked_count || 0, color: '#f43f5e' },
    { name: 'Escalated', count: stats.escalated_count || 0, color: '#f59e0b' },
  ];

  const demoScenarioMeta = {
    pay_demo_happy_path: {
      tag: 'CASE A',
      title: 'Approved Happy Path',
      desc: 'Transient UPI network timeout. Policy approves automated retry.',
      expected: 'APPROVED → RECOVERED',
      badgeColor: 'bg-emerald-50 text-emerald-800 border-emerald-300'
    },
    pay_demo_max_retries: {
      tag: 'CASE B',
      title: 'Max Retries Exceeded',
      desc: 'Retry counter = 4 (Limit 3). Policy blocks further automated retry attempts.',
      expected: 'BLOCKED (max_retry_exceeded)',
      badgeColor: 'bg-rose-50 text-rose-800 border-rose-300'
    },
    pay_demo_high_value: {
      tag: 'CASE C',
      title: 'High-Value Escalation',
      desc: 'Amount ₹75,000 exceeds ₹50,000 auto-recovery safety ceiling.',
      expected: 'ESCALATED (high_value_human_review)',
      badgeColor: 'bg-amber-50 text-amber-900 border-amber-300'
    },
    pay_demo_no_email: {
      tag: 'CASE D',
      title: 'Missing Contact Block',
      desc: 'Expired card requires link, but customer email is null.',
      expected: 'BLOCKED (missing_contact_info)',
      badgeColor: 'bg-rose-50 text-rose-800 border-rose-300'
    },
    pay_demo_low_conf: {
      tag: 'CASE E',
      title: 'Low AI Confidence',
      desc: 'Model certainty is 0.45 (< 0.60 safety threshold). Held for review.',
      expected: 'ESCALATED (low_confidence_escalate)',
      badgeColor: 'bg-amber-50 text-amber-900 border-amber-300'
    },
  };

  return (
    <div className="space-y-6">
      {/* Top Operations Header */}
      <div className="bg-slate-900 text-white rounded-xl p-6 shadow-sm border border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
              Razorpay AI Buildathon 2026
            </span>
            <span className="text-xs text-slate-400">Track: AI Revenue Recovery</span>
          </div>
          <h1 className="text-2xl font-black text-white mt-1.5 tracking-tight">
            Revenue Recovery Command Center
          </h1>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Autonomous risk detection, Gemini root-cause diagnosis, deterministic policy guardrails, and reproducible simulated execution benchmarked against synthetic ground truth.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          <button
            onClick={handleSeedData}
            disabled={isSeeding || isBatchRunning}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition flex items-center gap-2 disabled:opacity-50"
            title="Reset and re-seed 520 synthetic payments"
          >
            <Database className={`h-3.5 w-3.5 ${isSeeding ? 'animate-spin' : ''}`} />
            {isSeeding ? 'Seeding...' : 'Seed Dataset'}
          </button>
          <button
            onClick={handleRunBatch}
            disabled={isBatchRunning || isSeeding}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition shadow-xs flex items-center gap-2 disabled:opacity-50"
          >
            {isBatchRunning ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                Executing Batch...
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-white" />
                Run Recovery Batch
              </>
            )}
          </button>
        </div>
      </div>

      {/* Completion Notification */}
      {batchCompletedMsg && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs px-4 py-3 rounded-xl flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
          <span className="font-semibold">{batchCompletedMsg}</span>
        </div>
      )}

      {/* Primary Financial KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Revenue at Risk */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Revenue at Risk</span>
            <AlertTriangle className="h-4 w-4 text-rose-500" />
          </div>
          <div className="text-2xl font-black text-slate-950 font-numeric tracking-tight pt-0.5">
            {formatINRLakh(stats.total_at_risk)}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-100">
            <span>Total failed volume</span>
            <span className="font-semibold text-slate-800">{stats.total_payments} records</span>
          </div>
        </div>

        {/* GT Recoverable Pool */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-700">GT Recoverable Pool</span>
            <Cpu className="h-4 w-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-black text-indigo-950 font-numeric tracking-tight pt-0.5">
            {formatINRLakh(stats.ground_truth_recoverable_revenue)}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-100">
            <span>AI Predicted:</span>
            <span className="font-semibold text-slate-800">{formatINRLakh(stats.ai_predicted_recoverable_revenue)}</span>
          </div>
        </div>

        {/* Revenue Recovered */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700">Revenue Recovered</span>
            <TrendingUp className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-emerald-700 font-numeric tracking-tight pt-0.5">
            {formatINRLakh(stats.total_recovered)}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-100">
            <span>Measured recoveries</span>
            <span className="font-semibold text-emerald-700">{stats.successful_recovery_count || 0} successful</span>
          </div>
        </div>

        {/* Recovery Efficiency */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider text-purple-700">Recovery Efficiency</span>
            <Sparkles className="h-4 w-4 text-purple-500" />
          </div>
          <div className="text-2xl font-black text-purple-950 font-numeric tracking-tight pt-0.5">
            {formatPercent(stats.recovery_efficiency)}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-100">
            <span>Gross rate of risk</span>
            <span className="font-semibold text-slate-800">{formatPercent(stats.recovery_rate)}</span>
          </div>
        </div>
      </div>

      {/* Secondary Operational Telemetry Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Approved Actions
            </span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-xl font-bold text-emerald-600 font-numeric">{stats.approved_count || 0}</span>
              <span className="text-[11px] text-slate-500">
                ({formatPercentCompact(stats.approved_action_success_rate)} success conversion)
              </span>
            </div>
          </div>
          <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200">
            <CheckCircle2 className="h-4.5 w-4.5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Blocked by Policy
            </span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-xl font-bold text-rose-600 font-numeric">{stats.blocked_count || 0}</span>
              <span className="text-[11px] text-slate-500">
                ({formatPercentCompact(stats.policy_block_rate)} block rate)
              </span>
            </div>
          </div>
          <div className="p-2 rounded-lg bg-rose-50 text-rose-600 border border-rose-200">
            <XCircle className="h-4.5 w-4.5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Human Escalations
            </span>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-xl font-bold text-amber-600 font-numeric">{stats.escalated_count || 0}</span>
              <span className="text-[11px] text-slate-500">
                ({formatPercentCompact(stats.escalation_rate)} escalation rate)
              </span>
            </div>
          </div>
          <div className="p-2 rounded-lg bg-amber-50 text-amber-600 border border-amber-200">
            <ShieldAlert className="h-4.5 w-4.5" />
          </div>
        </div>
      </div>

      {/* Visual Recovery Funnel */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-5 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-indigo-600" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Autonomous Recovery Funnel Lifecycle
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-400">Sample: {stats.total_payments} Total Ingested</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-2 text-xs">
          {/* Stage 1 */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">1. Ingested Risk</span>
            <div className="font-bold text-sm text-slate-900 font-numeric">{formatINRLakh(stats.total_at_risk)}</div>
            <div className="text-[10px] text-slate-500">{stats.total_payments} payments at risk</div>
          </div>

          {/* Stage 2 */}
          <div className="p-3 rounded-lg bg-indigo-50/60 border border-indigo-200 space-y-1">
            <span className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider block">2. AI Diagnosed</span>
            <div className="font-bold text-sm text-indigo-950 font-numeric">{formatINRLakh(stats.ai_predicted_recoverable_revenue)}</div>
            <div className="text-[10px] text-indigo-700">Flagged recoverable</div>
          </div>

          {/* Stage 3 */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">3. Policy Gate</span>
            <div className="font-bold text-sm text-slate-900 font-numeric">{stats.approved_count || 0} Cleared</div>
            <div className="text-[10px] text-rose-600">{stats.blocked_count || 0} blocked / {stats.escalated_count || 0} esc.</div>
          </div>

          {/* Stage 4 */}
          <div className="p-3 rounded-lg bg-purple-50/60 border border-purple-200 space-y-1">
            <span className="text-[10px] font-bold text-purple-700 uppercase tracking-wider block">4. Simulated Run</span>
            <div className="font-bold text-sm text-purple-950 font-numeric">{stats.approved_count || 0} Attempts</div>
            <div className="text-[10px] text-purple-700">SHA-256 gateway physics</div>
          </div>

          {/* Stage 5 */}
          <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200 space-y-1">
            <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">5. Recovered</span>
            <div className="font-bold text-sm text-emerald-700 font-numeric">{formatINRLakh(stats.total_recovered)}</div>
            <div className="text-[10px] text-emerald-800 font-semibold">{formatPercent(stats.recovery_efficiency)} efficiency</div>
          </div>
        </div>
      </div>

      {/* Deterministic Demo Scenarios Section */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-950 uppercase tracking-wider">
                Deterministic Demonstration Scenarios
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200 uppercase">
                5 Guaranteed Test Cases
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Select any scenario card to inspect its exact end-to-end trace (Raw Failure → AI Proposal → Policy Gate → Simulator).
            </p>
          </div>
          <button 
            onClick={onViewPayments}
            className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            All Payments <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {demoCases.map((c) => {
            const meta = demoScenarioMeta[c.id] || {
              tag: 'CASE',
              title: c.id,
              desc: c.failure_reason,
              expected: 'EVALUATE',
              badgeColor: 'bg-slate-100 text-slate-700 border-slate-200'
            };
            return (
              <div
                key={c.id}
                onClick={() => onSelectPayment(c.id)}
                className="group relative p-4 rounded-lg border border-slate-200 hover:border-indigo-400 bg-white hover:bg-indigo-50/20 transition-all cursor-pointer shadow-2xs flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-slate-900 text-white tracking-wider">
                      {meta.tag}
                    </span>
                    <span className="font-mono text-xs font-bold text-slate-900 font-numeric">
                      {formatINR(c.amount)}
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                    {meta.title}
                  </h3>
                  <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                    {meta.desc}
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-slate-100">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Expected Policy:
                  </div>
                  <div className="text-[11px] font-mono font-medium text-slate-800 truncate mt-0.5">
                    {meta.expected}
                  </div>
                  <div className="flex items-center justify-end text-indigo-600 text-[11px] font-bold mt-2 group-hover:translate-x-0.5 transition-transform">
                    Inspect Trace <ArrowRight className="h-3 w-3 ml-0.5" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Analytics & Gemini Health Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Policy Decision Distribution Chart */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Policy Enforcement Distribution
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Breakdown of AI recommended interventions filtered by deterministic safety rules.
              </p>
            </div>
            <button
              onClick={onViewPolicy}
              className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
            >
              Policy Rules <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 h-60">
            <div className="h-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={policyChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <RechartsTooltip cursor={{ fill: '#f8fafc' }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {policyChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="h-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={policyChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="count"
                  >
                    {policyChartData.map((entry, index) => (
                      <Cell key={`pie-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend verticalAlign="bottom" height={32} iconSize={8} wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Gemini LLM Metrics Card */}
        <div className="bg-slate-900 text-white p-6 rounded-xl border border-slate-800 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                <h3 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
                  Gemini LLM Metrics
                </h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                gemini-3.5-flash
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-4 text-xs">
              <div className="bg-slate-800/70 p-3 rounded-lg border border-slate-700/70">
                <span className="text-[10px] text-slate-400 block uppercase font-semibold">Gemini Calls</span>
                <span className="text-xl font-bold text-white mt-0.5 block font-numeric">
                  {stats.llm_analyzed_count || 0}
                </span>
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  Fallback: {stats.heuristic_fallback_count || 0}
                </span>
              </div>

              <div className="bg-slate-800/70 p-3 rounded-lg border border-slate-700/70">
                <span className="text-[10px] text-slate-400 block uppercase font-semibold">LLM F1 Score</span>
                <span className="text-xl font-bold text-emerald-400 mt-0.5 block font-numeric">
                  {formatPercent(stats.llm_f1)}
                </span>
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  Precision: {formatPercent(stats.llm_precision)}
                </span>
              </div>

              <div className="bg-slate-800/70 p-3 rounded-lg border border-slate-700/70">
                <span className="text-[10px] text-slate-400 block uppercase font-semibold">LLM Recall</span>
                <span className="text-xl font-bold text-indigo-400 mt-0.5 block font-numeric">
                  {formatPercent(stats.llm_recall)}
                </span>
                <span className="text-[10px] text-slate-400 mt-0.5 block">Coverage</span>
              </div>

              <div className="bg-slate-800/70 p-3 rounded-lg border border-slate-700/70">
                <span className="text-[10px] text-slate-400 block uppercase font-semibold">Intervention Match</span>
                <span className="text-xl font-bold text-purple-400 mt-0.5 block font-numeric">
                  {formatPercent(stats.llm_intervention_accuracy)}
                </span>
                <span className="text-[10px] text-slate-400 mt-0.5 block">Exact match</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1 text-[11px]">
              <Info className="h-3.5 w-3.5 text-slate-400" />
              Isolated subset evaluation
            </span>
            <button 
              onClick={onViewEvaluation}
              className="text-indigo-400 hover:text-indigo-300 font-bold flex items-center gap-1 text-xs"
            >
              Benchmark Details <ArrowRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Recent Batch Ledger Preview */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-4 px-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Recent Recovery Interventions
            </h3>
            <p className="text-xs text-slate-500">Live operational ledger of analyzed and executed recovery actions.</p>
          </div>
          <button
            onClick={onViewPayments}
            className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            Explore Full Ledger <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase font-bold text-[10px]">
              <tr>
                <th className="px-6 py-3">Payment ID</th>
                <th className="px-6 py-3">Amount</th>
                <th className="px-6 py-3">AI Recommendation</th>
                <th className="px-6 py-3">Policy Gate</th>
                <th className="px-6 py-3">Simulated Outcome</th>
                <th className="px-6 py-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {recentResults.map((r) => {
                const decBadge = getDecisionBadge(r.policy_decision);
                const actBadge = getActionBadge(r.ai_recommendation);
                return (
                  <tr 
                    key={r.payment_id}
                    onClick={() => onSelectPayment(r.payment_id)}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-3 font-mono font-bold text-slate-900">
                      {r.payment_id}
                    </td>
                    <td className="px-6 py-3 text-slate-800 font-numeric font-semibold">
                      {formatINR(r.amount_recovered > 0 ? r.amount_recovered : undefined)}
                    </td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[11px] font-semibold ${actBadge.bg}`}>
                        {actBadge.label}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-extrabold ${decBadge.bg}`}>
                        {decBadge.label}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      {r.recovery_successful ? (
                        <span className="inline-flex items-center gap-1 font-bold text-emerald-700">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                          Recovered {formatINR(r.amount_recovered)}
                        </span>
                      ) : r.policy_decision === 'blocked' ? (
                        <span className="text-rose-700 font-semibold">Blocked by rule</span>
                      ) : r.policy_decision === 'escalated' ? (
                        <span className="text-amber-800 font-semibold">Escalated to human</span>
                      ) : (
                        <span className="text-slate-400">Failed retry</span>
                      )}
                    </td>
                    <td className="px-6 py-3 text-right">
                      <span className="text-indigo-600 font-bold hover:underline inline-flex items-center gap-0.5">
                        Trace <ArrowRight className="h-3 w-3" />
                      </span>
                    </td>
                  </tr>
                );
              })}
              {recentResults.length === 0 && (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-slate-400 text-xs">
                    No recent batch run records found. Click "Run Recovery Batch" above to start.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
