import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Sparkles, 
  ShieldCheck, 
  ShieldAlert, 
  ShieldX, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  Play, 
  RefreshCw, 
  Layers, 
  FileText, 
  Lock, 
  Database,
  ArrowDown,
  UserCheck
} from 'lucide-react';
import { getPayment, analyzePayment, getPaymentAudit } from '../api/client';
import { 
  formatINR, 
  formatDate, 
  formatPercent, 
  getMethodBadge, 
  getDecisionBadge, 
  getActionBadge 
} from '../utils/formatters';

export default function PaymentDetail({ paymentId, onBack }) {
  const [payment, setPayment] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  
  // Pipeline Results
  const [aiRec, setAiRec] = useState(null);
  const [policyDecision, setPolicyDecision] = useState(null);
  const [outcome, setOutcome] = useState(null);

  const fetchPaymentDetails = async () => {
    setLoading(true);
    setError('');
    try {
      const [paymentData, auditData] = await Promise.all([
        getPayment(paymentId),
        getPaymentAudit(paymentId).catch(() => [])
      ]);
      setPayment(paymentData);
      setAuditLogs(auditData || []);

      if (auditData && auditData.length > 0) {
        const aiEvent = auditData.find(e => e.event_type === 'ai_analysis');
        const policyEvent = auditData.find(e => e.event_type === 'policy_check');
        const executedEvent = auditData.find(e => e.event_type === 'action_executed');
        const blockedEvent = auditData.find(e => e.event_type === 'action_blocked');
        const escalatedEvent = auditData.find(e => e.event_type === 'escalated');

        if (aiEvent && aiEvent.details) {
          try {
            const aiDetails = typeof aiEvent.details === 'string' ? JSON.parse(aiEvent.details) : aiEvent.details;
            setAiRec(aiDetails);
          } catch {}
        }

        if (policyEvent && policyEvent.details) {
          try {
            const pDetails = typeof policyEvent.details === 'string' ? JSON.parse(policyEvent.details) : policyEvent.details;
            setPolicyDecision(pDetails);
          } catch {}
        }

        if (executedEvent && executedEvent.details) {
          try {
            const exDetails = typeof executedEvent.details === 'string' ? JSON.parse(executedEvent.details) : executedEvent.details;
            setOutcome({
              action_taken: exDetails.action,
              recovery_successful: exDetails.success,
              amount_recovered: exDetails.amount_recovered,
              details: exDetails.details,
            });
          } catch {}
        } else if (blockedEvent) {
          setOutcome({
            action_taken: 'blocked',
            recovery_successful: false,
            amount_recovered: 0,
            details: 'Recovery execution blocked by deterministic policy gate.',
          });
        } else if (escalatedEvent) {
          setOutcome({
            action_taken: 'escalated',
            recovery_successful: false,
            amount_recovered: 0,
            details: 'Held for manual human authorization and risk review.',
          });
        }
      }
    } catch (err) {
      console.error('Error loading payment detail:', err);
      setError('Failed to load payment transaction trace.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPaymentDetails();
  }, [paymentId]);

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const response = await analyzePayment(paymentId);
      setAiRec(response.ai_recommendation);
      setPolicyDecision(response.policy_decision);
      setOutcome({
        action_taken: response.action_taken,
        recovery_successful: response.recovery_successful,
        amount_recovered: response.amount_recovered,
        details: response.recovery_successful 
          ? `Successfully recovered ${formatINR(response.amount_recovered)}.` 
          : 'Action completed or blocked according to policy gate.',
      });

      const auditData = await getPaymentAudit(paymentId);
      setAuditLogs(auditData || []);
    } catch (err) {
      console.error('Pipeline execution error:', err);
      setError('Analysis pipeline execution failed.');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[440px]">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-7 w-7 text-indigo-600 animate-spin" />
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Loading Payment Decision Trace...
          </p>
        </div>
      </div>
    );
  }

  if (error && !payment) {
    return (
      <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">
        <button onClick={onBack} className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Dashboard
        </button>
        <div className="p-4 bg-rose-50 text-rose-800 text-xs rounded-lg border border-rose-200">
          {error}
        </div>
      </div>
    );
  }

  const mBadge = getMethodBadge(payment.payment_method);
  const isBlocked = policyDecision?.decision?.toLowerCase() === 'blocked';
  const isEscalated = policyDecision?.decision?.toLowerCase() === 'escalated';
  const isApproved = policyDecision?.decision?.toLowerCase() === 'approved';

  return (
    <div className="space-y-6">
      {/* Header & Context Bar */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <button 
            onClick={onBack}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition"
            title="Back to previous view"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-lg font-black text-slate-950">
                {payment.id}
              </span>
              <span className={`px-2 py-0.5 rounded border text-[11px] font-bold ${mBadge.bg}`}>
                {mBadge.label}
              </span>
              {payment.id.startsWith('pay_demo') && (
                <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-slate-900 text-white tracking-wider">
                  DEMO CASE
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5 font-medium">
              Customer: <span className="font-mono text-slate-800">{payment.customer_id}</span> · Ingested: {formatDate(payment.created_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunAnalysis}
            disabled={analyzing}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition shadow-xs flex items-center gap-2 disabled:opacity-50"
          >
            {analyzing ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                Processing Pipeline...
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-white" />
                {aiRec ? 'Re-run Decision Pipeline' : 'Run Decision Pipeline'}
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-4 rounded-xl">
          {error}
        </div>
      )}

      {/* Vertical Recovery Pipeline (The Visual Story) */}
      <div className="space-y-3">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2 px-1">
          <Layers className="h-4 w-4 text-indigo-600" />
          End-to-End Decision & Recovery Architecture
        </div>

        {/* STEP 1: PAYMENT CONTEXT */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="h-6 w-6 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center">
                1
              </span>
              <h3 className="text-xs font-bold text-slate-950 uppercase tracking-wider">Payment Context & Raw Gateway Signals</h3>
            </div>
            <span className="text-sm font-black font-mono text-slate-950 font-numeric">
              Amount: {formatINR(payment.amount)}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 text-xs">
            <div>
              <span className="text-slate-400 block font-semibold text-[10px] uppercase">Failure Reason</span>
              <span className="font-mono font-bold text-rose-600 text-xs mt-0.5 block">
                {payment.failure_reason || 'unknown'}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block font-semibold text-[10px] uppercase">Retry History</span>
              <span className="font-mono font-bold text-slate-800 text-xs mt-0.5 block">
                {payment.retry_count} / 3 prior retries
              </span>
            </div>
            <div>
              <span className="text-slate-400 block font-semibold text-[10px] uppercase">Customer Ratio</span>
              <span className="font-bold text-slate-800 text-xs mt-0.5 block">
                {payment.previous_success_count || 0} successes / {payment.previous_failure_count || 0} fails
              </span>
            </div>
            <div>
              <span className="text-slate-400 block font-semibold text-[10px] uppercase">Contact Details</span>
              <span className="font-medium text-slate-800 text-xs mt-0.5 block truncate">
                {payment.customer_email || <span className="text-slate-400 italic font-normal">None Available</span>}
              </span>
            </div>
          </div>
        </div>

        {/* Arrow connector */}
        <div className="flex justify-center -my-1.5 relative z-10">
          <div className="p-1 rounded-full bg-slate-100 border border-slate-300 text-slate-500 shadow-2xs">
            <ArrowDown className="h-3.5 w-3.5" />
          </div>
        </div>

        {/* STEP 2: AI ROOT-CAUSE DIAGNOSIS & PROPOSAL */}
        <div className="bg-white rounded-xl border border-indigo-200 shadow-2xs p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 px-3 py-1 bg-indigo-50 text-indigo-700 text-[10px] font-bold border-b border-l border-indigo-200 rounded-bl-lg flex items-center gap-1">
            <Sparkles className="h-3 w-3" />
            Advisory Proposal
          </div>

          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <span className="h-6 w-6 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center">
              2
            </span>
            <h3 className="text-xs font-bold text-indigo-950 uppercase tracking-wider">AI Root-Cause Diagnosis & Proposed Action</h3>
          </div>

          {aiRec ? (
            <div className="mt-4 space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <span className="text-slate-400 block font-semibold text-[10px] uppercase">Diagnosed Root Cause</span>
                  <span className="font-bold text-slate-900 mt-0.5 block">
                    {aiRec.root_cause}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block font-semibold text-[10px] uppercase">Recommended Action</span>
                  <span className="mt-0.5 inline-block">
                    {(() => {
                      const b = getActionBadge(aiRec.recommendation);
                      return (
                        <span className={`px-2 py-0.5 rounded border font-bold ${b.bg}`}>
                          {b.label}
                        </span>
                      );
                    })()}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block font-semibold text-[10px] uppercase">Self-Reported Confidence</span>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 bg-slate-100 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          aiRec.confidence >= 0.70 ? 'bg-emerald-500' : aiRec.confidence >= 0.50 ? 'bg-amber-500' : 'bg-rose-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(5, aiRec.confidence * 100))}%` }}
                      />
                    </div>
                    <span className="font-mono font-bold text-slate-800 text-[11px]">
                      {(aiRec.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="text-[10px] font-bold text-slate-500 uppercase block mb-0.5">Model Explanation:</span>
                <p className="text-slate-700 text-xs leading-relaxed font-medium">
                  {aiRec.explanation}
                </p>
              </div>
            </div>
          ) : (
            <div className="py-6 text-center text-slate-400 text-xs font-medium">
              Click "Run Decision Pipeline" above to execute AI diagnosis.
            </div>
          )}
        </div>

        {/* Arrow connector */}
        <div className="flex justify-center -my-1.5 relative z-10">
          <div className="p-1 rounded-full bg-slate-100 border border-slate-300 text-slate-500 shadow-2xs">
            <ArrowDown className="h-3.5 w-3.5" />
          </div>
        </div>

        {/* STEP 3 & 4: DETERMINISTIC POLICY GATE & FINAL DECISION */}
        <div className={`rounded-xl shadow-2xs p-5 border-2 transition-all ${
          isBlocked 
            ? 'bg-rose-50/40 border-rose-300' 
            : isEscalated 
            ? 'bg-amber-50/40 border-amber-300' 
            : isApproved 
            ? 'bg-emerald-50/40 border-emerald-300' 
            : 'bg-white border-slate-200'
        }`}>
          <div className="flex items-center justify-between pb-3 border-b border-slate-200/80">
            <div className="flex items-center gap-2">
              <span className={`h-6 w-6 rounded-full font-bold text-xs flex items-center justify-center ${
                isBlocked ? 'bg-rose-600 text-white' : isEscalated ? 'bg-amber-500 text-white' : isApproved ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-700'
              }`}>
                3
              </span>
              <h3 className="text-xs font-bold text-slate-950 uppercase tracking-wider">Deterministic Safety Policy Gate & Final Authority</h3>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              Deterministic Authority
            </span>
          </div>

          {policyDecision ? (
            <div className="mt-4 space-y-3 text-xs">
              {/* Decision Callout Badge */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <span className="text-slate-500 block font-bold text-[10px] uppercase">Final Gate Decision:</span>
                  <div className="mt-1">
                    {(() => {
                      const dec = getDecisionBadge(policyDecision.decision);
                      return (
                        <span className={`px-3 py-1 rounded-md text-xs font-black uppercase tracking-wider border ${dec.bg}`}>
                          {dec.label}
                        </span>
                      );
                    })()}
                  </div>
                </div>

                {isBlocked && (
                  <div className="flex items-center gap-1.5 text-rose-800 font-bold text-xs bg-rose-100/90 px-3 py-1.5 rounded-lg border border-rose-300">
                    <ShieldX className="h-4 w-4 text-rose-600" />
                    AI Action Overruled by Financial Guardrail
                  </div>
                )}
                {isEscalated && (
                  <div className="flex items-center gap-1.5 text-amber-900 font-bold text-xs bg-amber-100/90 px-3 py-1.5 rounded-lg border border-amber-300">
                    <ShieldAlert className="h-4 w-4 text-amber-600" />
                    Requires Manual Operations Console Approval
                  </div>
                )}
                {isApproved && (
                  <div className="flex items-center gap-1.5 text-emerald-900 font-bold text-xs bg-emerald-100/90 px-3 py-1.5 rounded-lg border border-emerald-300">
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                    Cleared All Deterministic Safety Invariants
                  </div>
                )}
              </div>

              {/* Triggered Policy Rules */}
              {policyDecision.triggered_rules && policyDecision.triggered_rules.length > 0 ? (
                <div className={`p-3.5 rounded-lg border ${
                  isBlocked ? 'bg-rose-100/70 border-rose-300 text-rose-950' : 'bg-amber-100/70 border-amber-300 text-amber-950'
                }`}>
                  <span className="font-bold text-[11px] block mb-1">
                    {isBlocked ? 'Triggered Blocking Invariant(s):' : 'Triggered Escalation Invariant(s):'}
                  </span>
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {policyDecision.triggered_rules.map((rule, idx) => (
                      <span key={idx} className="font-mono text-[11px] font-bold px-2 py-0.5 bg-white rounded border border-slate-300">
                        {rule}
                      </span>
                    ))}
                  </div>
                  {policyDecision.reasons && policyDecision.reasons.length > 0 && (
                    <ul className="list-disc pl-4 space-y-0.5 text-slate-800 text-[11px]">
                      {policyDecision.reasons.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : (
                <div className="p-3 bg-emerald-50 text-emerald-900 rounded-lg border border-emerald-200 text-xs font-medium">
                  ✓ Retry permitted · ✓ Below retry limit (3) · ✓ Confidence above threshold (60%) · ✓ Below high-value cap (₹50,000)
                </div>
              )}
            </div>
          ) : (
            <div className="py-6 text-center text-slate-400 text-xs font-medium">
              Policy evaluation pending pipeline execution.
            </div>
          )}
        </div>

        {/* Arrow connector */}
        <div className="flex justify-center -my-1.5 relative z-10">
          <div className="p-1 rounded-full bg-slate-100 border border-slate-300 text-slate-500 shadow-2xs">
            <ArrowDown className="h-3.5 w-3.5" />
          </div>
        </div>

        {/* STEP 5: SIMULATED EXECUTION & MEASURED RECOVERY OUTCOME */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="h-6 w-6 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center">
                4
              </span>
              <h3 className="text-xs font-bold text-slate-950 uppercase tracking-wider">Simulated Execution & Measured Recovery Outcome</h3>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              SHA-256 Simulation
            </span>
          </div>

          {outcome ? (
            <div className="mt-4 space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <span className="text-slate-400 block font-semibold text-[10px] uppercase">Executed Action</span>
                  <span className="font-mono font-bold text-slate-900 text-xs mt-0.5 block">
                    {outcome.action_taken}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block font-semibold text-[10px] uppercase">Recovery Status</span>
                  <div className="mt-0.5">
                    {outcome.recovery_successful ? (
                      <span className="inline-flex items-center gap-1 text-emerald-800 font-bold bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> SUCCESSFUL RECOVERY
                      </span>
                    ) : isBlocked ? (
                      <span className="inline-flex items-center gap-1 text-rose-800 font-bold bg-rose-50 px-2.5 py-0.5 rounded border border-rose-200">
                        <XCircle className="h-3.5 w-3.5 text-rose-600" /> NO ACTION (BLOCKED BY POLICY)
                      </span>
                    ) : isEscalated ? (
                      <span className="inline-flex items-center gap-1 text-amber-900 font-bold bg-amber-50 px-2.5 py-0.5 rounded border border-amber-200">
                        <AlertTriangle className="h-3.5 w-3.5 text-amber-600" /> HELD FOR OPERATOR REVIEW
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-slate-700 font-bold bg-slate-100 px-2.5 py-0.5 rounded">
                        RECOVERY ATTEMPT FAILED
                      </span>
                    )}
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 block font-semibold text-[10px] uppercase">Measured Revenue Recovered</span>
                  <span className={`text-base font-black font-mono mt-0.5 block font-numeric ${
                    outcome.amount_recovered > 0 ? 'text-emerald-700' : 'text-slate-400'
                  }`}>
                    {formatINR(outcome.amount_recovered)}
                  </span>
                </div>
              </div>

              {outcome.details && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-slate-700">
                  <span className="font-bold text-slate-500 block text-[10px] uppercase">Simulation Telemetry:</span>
                  <p className="mt-0.5 text-xs font-mono">{outcome.details}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="py-6 text-center text-slate-400 text-xs font-medium">
              Simulation execution pending pipeline run.
            </div>
          )}
        </div>
      </div>

      {/* Immutable Audit Trail Timeline */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-slate-600" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Immutable Audit Trail</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">{auditLogs.length} audit entries</span>
        </div>

        {auditLogs.length > 0 ? (
          <div className="space-y-2.5">
            {auditLogs.map((log, idx) => {
              let parsedDetails = null;
              try {
                parsedDetails = typeof log.details === 'string' ? JSON.parse(log.details) : log.details;
              } catch {}

              return (
                <div key={log.id || idx} className="p-3.5 bg-slate-50/80 rounded-lg border border-slate-200 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-indigo-800 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 text-[10px] uppercase">
                        {log.event_type}
                      </span>
                      <span className="text-slate-500 text-[11px] font-mono">
                        {formatDate(log.created_at)}
                      </span>
                    </div>
                  </div>
                  {parsedDetails && (
                    <pre className="text-[11px] font-mono text-slate-800 bg-white p-2.5 rounded border border-slate-200 max-h-36 overflow-y-auto">
                      {JSON.stringify(parsedDetails, null, 2)}
                    </pre>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-6 text-slate-400 text-xs font-medium">
            No audit records logged for this payment yet.
          </div>
        )}
      </div>
    </div>
  );
}
