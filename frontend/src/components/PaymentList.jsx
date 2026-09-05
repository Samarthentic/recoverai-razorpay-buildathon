import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  ChevronLeft, 
  ChevronRight, 
  ArrowRight, 
  RefreshCw,
  SlidersHorizontal,
  Info,
  CreditCard
} from 'lucide-react';
import { getPayments } from '../api/client';
import { 
  formatINR, 
  formatDate, 
  getMethodBadge, 
  getActionBadge 
} from '../utils/formatters';

export default function PaymentList({ onSelectPayment }) {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [methodFilter, setMethodFilter] = useState('all');
  const [skip, setSkip] = useState(0);
  const limit = 15;

  const fetchPaymentsList = async () => {
    try {
      setLoading(true);
      const data = await getPayments({
        skip,
        limit,
        status: 'failed',
      });
      setPayments(data || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching payments ledger:', err);
      setError('Failed to load payments ledger.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPaymentsList();
  }, [skip]);

  const filteredPayments = payments.filter((p) => {
    const matchesSearch = !search || 
      p.id.toLowerCase().includes(search.toLowerCase()) || 
      (p.customer_id && p.customer_id.toLowerCase().includes(search.toLowerCase())) ||
      (p.customer_email && p.customer_email.toLowerCase().includes(search.toLowerCase())) ||
      (p.failure_reason && p.failure_reason.toLowerCase().includes(search.toLowerCase()));

    const matchesMethod = methodFilter === 'all' || p.payment_method.toLowerCase() === methodFilter.toLowerCase();

    return matchesSearch && matchesMethod;
  });

  const handlePrev = () => setSkip((prev) => Math.max(0, prev - limit));
  const handleNext = () => setSkip((prev) => prev + limit);

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-indigo-600" />
            <h1 className="text-lg font-bold text-slate-950">At-Risk Payments Ledger</h1>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Operational ledger of failed transactions requiring diagnostic analysis and policy-governed recovery.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          {/* Search bar */}
          <div className="relative min-w-[240px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search ID, email, reason..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8.5 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-slate-900 focus:bg-white transition"
            />
          </div>

          {/* Payment Method Filter */}
          <div className="relative">
            <select
              value={methodFilter}
              onChange={(e) => setMethodFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-900 appearance-none pr-8 cursor-pointer"
            >
              <option value="all">All Methods</option>
              <option value="upi">UPI</option>
              <option value="card">Cards</option>
              <option value="netbanking">Netbanking</option>
              <option value="wallet">Wallets</option>
              <option value="emandate">eMandate</option>
            </select>
            <Filter className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
          </div>

          {/* Refresh Button */}
          <button
            onClick={fetchPaymentsList}
            disabled={loading}
            className="p-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-600 transition"
            title="Refresh list"
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

      {/* Table Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase font-bold text-[10px]">
              <tr>
                <th className="px-5 py-3">Payment ID</th>
                <th className="px-5 py-3">Amount</th>
                <th className="px-5 py-3">Method</th>
                <th className="px-5 py-3">Failure Reason</th>
                <th className="px-5 py-3 text-center">Retries</th>
                <th className="px-5 py-3">Customer Contact</th>
                <th className="px-5 py-3">Synthetic Benchmark</th>
                <th className="px-5 py-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {loading ? (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center text-slate-400">
                    <RefreshCw className="h-6 w-6 text-indigo-600 animate-spin mx-auto mb-2" />
                    Loading payment records...
                  </td>
                </tr>
              ) : filteredPayments.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center text-slate-400">
                    No matching payment records found.
                  </td>
                </tr>
              ) : (
                filteredPayments.map((p) => {
                  const mBadge = getMethodBadge(p.payment_method);
                  const gtBadge = getActionBadge(p.ground_truth_best_action);
                  return (
                    <tr
                      key={p.id}
                      onClick={() => onSelectPayment(p.id)}
                      className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                    >
                      {/* Payment ID */}
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-bold text-slate-900">
                            {p.id}
                          </span>
                          {p.id.startsWith('pay_demo') && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] font-extrabold bg-slate-900 text-white">
                              DEMO
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {p.customer_id}
                        </div>
                      </td>

                      {/* Amount */}
                      <td className="px-5 py-3.5">
                        <span className="font-black text-slate-950 font-numeric">
                          {formatINR(p.amount)}
                        </span>
                      </td>

                      {/* Method */}
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[11px] font-bold ${mBadge.bg}`}>
                          {mBadge.label}
                        </span>
                      </td>

                      {/* Failure Reason */}
                      <td className="px-5 py-3.5">
                        <span className="font-mono text-rose-600 font-semibold text-[11px] block">
                          {p.failure_reason || 'unknown'}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {formatDate(p.created_at)}
                        </span>
                      </td>

                      {/* Retry count */}
                      <td className="px-5 py-3.5 text-center">
                        <span className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] ${
                          p.retry_count >= 3 
                            ? 'bg-rose-100 text-rose-800' 
                            : p.retry_count > 0 
                            ? 'bg-amber-100 text-amber-900' 
                            : 'bg-slate-100 text-slate-700'
                        }`}>
                          {p.retry_count} / 3
                        </span>
                      </td>

                      {/* Customer Email */}
                      <td className="px-5 py-3.5 text-slate-700 text-[11px]">
                        {p.customer_email ? (
                          <span className="truncate max-w-[160px] block font-medium">{p.customer_email}</span>
                        ) : (
                          <span className="text-slate-400 italic">No email</span>
                        )}
                      </td>

                      {/* Ground Truth benchmark indicator */}
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-1.5">
                          <span className={`h-2 w-2 rounded-full ${
                            p.ground_truth_recoverable ? 'bg-emerald-500' : 'bg-slate-300'
                          }`} />
                          <span className={`text-[11px] font-bold ${
                            p.ground_truth_recoverable ? 'text-emerald-800' : 'text-slate-500'
                          }`}>
                            {p.ground_truth_recoverable ? 'Recoverable' : 'Unrecoverable'}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          Optimal: <span className="font-semibold text-slate-700">{gtBadge.label}</span>
                        </div>
                      </td>

                      {/* CTA */}
                      <td className="px-5 py-3.5 text-right">
                        <span className="text-indigo-600 font-bold hover:text-indigo-800 inline-flex items-center gap-1 text-[11px]">
                          Inspect <ArrowRight className="h-3 w-3" />
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3.5 px-6 border-t border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div className="text-xs text-slate-500 font-medium">
            Showing <span className="font-bold text-slate-800">{filteredPayments.length}</span> payments (Offset: {skip})
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
              disabled={payments.length < limit || loading}
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
