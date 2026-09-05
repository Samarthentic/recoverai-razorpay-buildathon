/**
 * Currency, number, and status formatting utilities for RecoverAI.
 * All backend monetary amounts are stored in paise (1 INR = 100 paise).
 */

export function formatINR(paise, includeDecimals = false) {
  if (paise === undefined || paise === null) return '₹0';
  const rupees = paise / 100;
  if (includeDecimals) {
    return `₹${rupees.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `₹${Math.round(rupees).toLocaleString('en-IN')}`;
}

export function formatINRLakh(paise) {
  if (paise === undefined || paise === null) return '₹0';
  const rupees = paise / 100;
  if (rupees >= 100000) {
    const lakhs = rupees / 100000;
    return `₹${lakhs.toFixed(2)}L`;
  }
  if (rupees >= 1000) {
    return `₹${(rupees / 1000).toFixed(1)}k`;
  }
  return `₹${rupees.toLocaleString('en-IN')}`;
}

export function formatPercent(value) {
  if (value === undefined || value === null) return '0.00%';
  return `${Number(value).toFixed(2)}%`;
}

export function formatPercentCompact(value) {
  if (value === undefined || value === null) return '0%';
  return `${Number(value).toFixed(1)}%`;
}

export function formatDate(dateString) {
  if (!dateString) return '-';
  try {
    const d = new Date(dateString);
    return d.toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return dateString;
  }
}

export function formatDateShort(dateString) {
  if (!dateString) return '-';
  try {
    const d = new Date(dateString);
    return d.toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

export function getMethodBadge(method) {
  const m = (method || '').toLowerCase();
  switch (m) {
    case 'upi':
      return { label: 'UPI', bg: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
    case 'card':
      return { label: 'Card', bg: 'bg-blue-50 text-blue-800 border-blue-200' };
    case 'netbanking':
      return { label: 'Netbanking', bg: 'bg-purple-50 text-purple-800 border-purple-200' };
    case 'wallet':
      return { label: 'Wallet', bg: 'bg-amber-50 text-amber-800 border-amber-200' };
    case 'emandate':
      return { label: 'eMandate', bg: 'bg-slate-100 text-slate-800 border-slate-200' };
    default:
      return { label: method || 'Unknown', bg: 'bg-slate-50 text-slate-700 border-slate-200' };
  }
}

export function getDecisionBadge(decision) {
  const d = (decision || '').toLowerCase();
  switch (d) {
    case 'approved':
      return { label: 'APPROVED', bg: 'bg-emerald-50 text-emerald-800 border-emerald-300' };
    case 'blocked':
      return { label: 'BLOCKED', bg: 'bg-rose-50 text-rose-800 border-rose-300' };
    case 'escalated':
      return { label: 'ESCALATED', bg: 'bg-amber-50 text-amber-900 border-amber-300' };
    default:
      return { label: (decision || 'PENDING').toUpperCase(), bg: 'bg-slate-100 text-slate-800 border-slate-300' };
  }
}

export function getActionBadge(action) {
  const a = (action || '').toLowerCase();
  switch (a) {
    case 'retry_payment':
      return { label: 'Retry Payment', bg: 'bg-indigo-50 text-indigo-800 border-indigo-200' };
    case 'send_payment_link':
      return { label: 'Payment Link', bg: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
    case 'send_reminder':
      return { label: 'Send Reminder', bg: 'bg-amber-50 text-amber-900 border-amber-200' };
    case 'offer_alternative_method':
      return { label: 'Alt Method', bg: 'bg-purple-50 text-purple-800 border-purple-200' };
    case 'escalate_to_human':
      return { label: 'Human Review', bg: 'bg-orange-50 text-orange-800 border-orange-200' };
    case 'do_not_retry':
      return { label: 'Do Not Retry', bg: 'bg-slate-100 text-slate-700 border-slate-300' };
    default:
      return { label: action || '-', bg: 'bg-slate-50 text-slate-700 border-slate-200' };
  }
}
