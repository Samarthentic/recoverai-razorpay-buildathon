import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  ChevronLeft, 
  ChevronRight, 
  ChevronDown, 
  ChevronRight as ChevronRightIcon,
  Clock,
  RefreshCw,
  FileCode,
  ArrowRight
} from 'lucide-react';
import { getAuditLogs } from '../api/client';
import { formatDate } from '../utils/formatters';

const eventTypeStyles = {
  ai_analysis: { label: 'AI Diagnosis', bg: 'bg-indigo-50 text-indigo-800 border-indigo-200' },
  policy_check: { label: 'Policy Check', bg: 'bg-purple-50 text-purple-800 border-purple-200' },
  action_executed: { label: 'Action Executed', bg: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
  action_blocked: { label: 'Action Blocked', bg: 'bg-rose-50 text-rose-800 border-rose-200' },
  escalated: { label: 'Escalated', bg: 'bg-amber-50 text-amber-900 border-amber-200' },
  error: { label: 'System Error', bg: 'bg-red-100 text-red-900 border-red-300' },
};

export default function AuditTrail({ onSelectPayment }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});
  
  const [searchTerm, setSearchTerm] = useState('');
  const [eventType, setEventType] = useState('all');
  const [skip, setSkip] = useState(0);
  const limit = 15;

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await getAuditLogs({
        skip,
        limit,
        payment_id: searchTerm.trim() || undefined,
        event_type: eventType !== 'all' ? eventType : undefined,
      });
      setLogs(data || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching audit trail records:', err);
      setError('Failed to load audit trail ledger.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [skip, eventType]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setSkip(0);
    fetchLogs();
  };

  const handleEventTypeChange = (e) => {
    setEventType(e.target.value);
    setSkip(0);
  };

  const toggleRow = (id) => {
    setExpandedRows((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handlePrev = () => setSkip((prev) => Math.max(0, prev - limit));
  const handleNext = () => setSkip((prev) => prev + limit);

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-indigo-600" />
            <h1 className="text-lg font-bold text-slate-950">Immutable Audit Trail</h1>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Structured, append-only operational ledger recording every AI diagnosis, policy check, and simulation execution.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          {/* Event Type Filter */}
          <div className="relative">
            <select
              value={eventType}
              onChange={handleEventTypeChange}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-900 appearance-none pr-8 cursor-pointer"
            >
              <option value="all">All Events</option>
              <option value="ai_analysis">AI Analysis</option>
              <option value="policy_check">Policy Check</option>
              <option value="action_executed">Action Executed</option>
              <option value="action_blocked">Action Blocked</option>
              <option value="escalated">Escalated</option>
              <option value="error">Errors</option>
            </select>
            <Filter className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
          </div>

          {/* Payment ID Search */}
          <form onSubmit={handleSearchSubmit} className="relative min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search Payment ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8.5 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-slate-900 focus:bg-white transition"
            />
          </form>

          {/* Refresh */}
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="p-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-600 transition"
            title="Refresh logs"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-4 rounded-xl">
          {error}
        </div>
      )}

      {/* Audit Log Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase font-bold text-[10px]">
              <tr>
                <th className="px-4 py-3 w-8"></th>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">Payment ID</th>
                <th className="px-4 py-3">Event Type</th>
                <th className="px-4 py-3">Event Summary</th>
                <th className="px-4 py-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-slate-400">
                    <RefreshCw className="h-6 w-6 text-indigo-600 animate-spin mx-auto mb-2" />
                    Loading audit trail events...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-slate-400">
                    No audit records match the selected filters.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  let parsed = {};
                  try {
                    parsed = typeof log.details === 'string' ? JSON.parse(log.details) : log.details || {};
                  } catch {
                    parsed = { raw: log.details };
                  }

                  const isExpanded = !!expandedRows[log.id];
                  const style = eventTypeStyles[log.event_type] || {
                    label: log.event_type,
                    bg: 'bg-slate-100 text-slate-700 border-slate-200'
                  };

                  let summaryText = '-';
                  if (log.event_type === 'ai_analysis') {
                    summaryText = `AI suggested: ${parsed.recommendation || 'unknown'} (confidence: ${parsed.confidence ? (parsed.confidence * 100).toFixed(0) + '%' : '-'})`;
                  } else if (log.event_type === 'policy_check') {
                    summaryText = `Policy outcome: ${parsed.decision ? parsed.decision.toUpperCase() : '-'} (${(parsed.triggered_rules || []).join(', ') || 'No violations'})`;
                  } else if (log.event_type === 'action_executed') {
                    summaryText = `Simulated ${parsed.action} → ${parsed.success ? `Success (₹${(parsed.amount_recovered/100).toFixed(2)})` : 'Failed'}`;
                  } else if (log.event_type === 'action_blocked') {
                    summaryText = `Blocked action: ${parsed.intended_action} (${(parsed.triggered_rules || []).join(', ')})`;
                  } else if (log.event_type === 'escalated') {
                    summaryText = `Escalated ${parsed.intended_action} (${(parsed.triggered_rules || []).join(', ')})`;
                  } else if (parsed.error) {
                    summaryText = `Error: ${parsed.error}`;
                  }

                  return (
                    <React.Fragment key={log.id}>
                      <tr 
                        className={`hover:bg-slate-50/80 cursor-pointer transition-colors ${
                          isExpanded ? 'bg-slate-50/60' : ''
                        }`}
                        onClick={() => toggleRow(log.id)}
                      >
                        <td className="px-4 py-3 text-slate-400">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-indigo-600" />
                          ) : (
                            <ChevronRightIcon className="h-4 w-4" />
                          )}
                        </td>
                        <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                          {formatDate(log.created_at)}
                        </td>
                        <td className="px-4 py-3">
                          {log.payment_id ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onSelectPayment(log.payment_id);
                              }}
                              className="font-mono font-bold text-indigo-600 hover:underline inline-flex items-center gap-1"
                            >
                              {log.payment_id}
                              <ArrowRight className="h-3 w-3" />
                            </button>
                          ) : (
                            <span className="text-slate-400 italic">System event</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-extrabold uppercase tracking-wider ${style.bg}`}>
                            {style.label}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-800 text-[11px] truncate max-w-md font-medium">
                          {summaryText}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="text-slate-400 font-mono text-[11px] hover:text-slate-700">
                            {isExpanded ? 'Collapse' : 'Inspect'}
                          </span>
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr className="bg-slate-900 text-slate-200">
                          <td colSpan="6" className="p-4 px-8 border-b border-slate-800">
                            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                              <span className="flex items-center gap-1.5 font-bold font-mono">
                                <FileCode className="h-4 w-4 text-indigo-400" />
                                Audit Event Payload JSON (Event #{log.id})
                              </span>
                              <span className="font-mono text-[11px]">Batch ID: {log.batch_id || 'manual_run'}</span>
                            </div>
                            <pre className="font-mono text-xs text-emerald-400 bg-slate-950 p-3.5 rounded-lg overflow-x-auto border border-slate-800">
                              {JSON.stringify(parsed, null, 2)}
                            </pre>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-3.5 px-6 border-t border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div className="text-xs text-slate-500 font-medium">
            Showing <span className="font-bold text-slate-800">{logs.length}</span> entries (Offset: {skip})
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={handlePrev}
              disabled={skip === 0 || loading}
              className="px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition flex items-center gap-1"
            >
              <ChevronLeft className="h-3.5 w-3.5" /> Previous
            </button>
            <button
              onClick={handleNext}
              disabled={logs.length < limit || loading}
              className="px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-100 disabled:opacity-40 transition flex items-center gap-1"
            >
              Next <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
