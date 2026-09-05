import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CreditCard, 
  ShieldCheck, 
  Target, 
  Clock, 
  Server,
  Layers,
  ChevronRight
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import PaymentList from './components/PaymentList';
import PaymentDetail from './components/PaymentDetail';
import PolicyControls from './components/PolicyControls';
import Evaluation from './components/Evaluation';
import AuditTrail from './components/AuditTrail';
import { getSystemStatus } from './api/client';

function App() {
  const [currentView, setCurrentView] = useState('dashboard'); // dashboard, payments, policy, evaluation, audit, detail
  const [selectedPaymentId, setSelectedPaymentId] = useState(null);
  const [previousView, setPreviousView] = useState('dashboard');
  const [systemHealth, setSystemHealth] = useState(null);

  useEffect(() => {
    getSystemStatus()
      .then(setSystemHealth)
      .catch(() => setSystemHealth(null));
  }, []);

  const handleSelectPayment = (paymentId) => {
    setPreviousView(currentView === 'detail' ? 'dashboard' : currentView);
    setSelectedPaymentId(paymentId);
    setCurrentView('detail');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackFromDetail = () => {
    setCurrentView(previousView);
    setSelectedPaymentId(null);
  };

  const isGeminiConnected = systemHealth?.components?.gemini_analysis === 'connected';

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans antialiased selection:bg-indigo-100 selection:text-indigo-900">
      {/* Top Environment Warning Strip */}
      <div className="bg-slate-950 text-slate-300 text-[11px] py-1.5 px-4 border-b border-slate-800 text-center font-medium tracking-wide flex items-center justify-center gap-2">
        <span className="inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
          SIMULATION ENVIRONMENT
        </span>
        <span>Synthetic Data · Deterministic Gateway Physics · No Real Transactions</span>
      </div>

      {/* Main Navigation Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand Logo & Tagline */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  setCurrentView('dashboard');
                  setSelectedPaymentId(null);
                }}
                className="flex items-center gap-2.5 text-left group focus:outline-none"
              >
                <div className="h-9 w-9 rounded-lg bg-slate-900 flex items-center justify-center text-white border border-slate-800 shadow-sm group-hover:bg-indigo-950 transition">
                  <Activity className="h-4.5 w-4.5 text-indigo-400" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-base font-black tracking-tight text-slate-950">
                      Recover<span className="text-indigo-600">AI</span>
                    </span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                      CONTROL PLANE
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 font-medium -mt-0.5">
                    AI Revenue Recovery Operations Console
                  </p>
                </div>
              </button>
            </div>

            {/* Navigation Tabs */}
            <nav className="flex items-center gap-1">
              <button
                onClick={() => {
                  setCurrentView('dashboard');
                  setSelectedPaymentId(null);
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5 ${
                  currentView === 'dashboard'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-950 hover:bg-slate-100'
                }`}
              >
                <Activity className="h-3.5 w-3.5" />
                Overview
              </button>

              <button
                onClick={() => {
                  setCurrentView('payments');
                  setSelectedPaymentId(null);
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5 ${
                  currentView === 'payments'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-950 hover:bg-slate-100'
                }`}
              >
                <CreditCard className="h-3.5 w-3.5" />
                Payments
              </button>

              <button
                onClick={() => {
                  setCurrentView('policy');
                  setSelectedPaymentId(null);
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5 ${
                  currentView === 'policy'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-950 hover:bg-slate-100'
                }`}
              >
                <ShieldCheck className="h-3.5 w-3.5" />
                Policy & Controls
              </button>

              <button
                onClick={() => {
                  setCurrentView('evaluation');
                  setSelectedPaymentId(null);
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5 ${
                  currentView === 'evaluation'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-950 hover:bg-slate-100'
                }`}
              >
                <Target className="h-3.5 w-3.5" />
                Evaluation
              </button>

              <button
                onClick={() => {
                  setCurrentView('audit');
                  setSelectedPaymentId(null);
                }}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5 ${
                  currentView === 'audit'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-950 hover:bg-slate-100'
                }`}
              >
                <Clock className="h-3.5 w-3.5" />
                Audit Trail
              </button>
            </nav>

            {/* Telemetry Status Indicator */}
            <div className="hidden lg:flex items-center gap-2 pl-3 border-l border-slate-200">
              <button
                onClick={() => {
                  setCurrentView('policy');
                  setSelectedPaymentId(null);
                }}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 transition"
                title="View active engine health and policy parameters"
              >
                <span className={`h-2 w-2 rounded-full ${
                  isGeminiConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                }`} />
                <span>
                  {isGeminiConnected ? 'Engine: Live Gemini' : 'Engine: Fallback Active'}
                </span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content View Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentView === 'dashboard' && (
          <Dashboard
            onSelectPayment={handleSelectPayment}
            onViewPayments={() => setCurrentView('payments')}
            onViewEvaluation={() => setCurrentView('evaluation')}
            onViewAudit={() => setCurrentView('audit')}
            onViewPolicy={() => setCurrentView('policy')}
          />
        )}

        {currentView === 'payments' && (
          <PaymentList onSelectPayment={handleSelectPayment} />
        )}

        {currentView === 'policy' && (
          <PolicyControls />
        )}

        {currentView === 'evaluation' && (
          <Evaluation />
        )}

        {currentView === 'audit' && (
          <AuditTrail onSelectPayment={handleSelectPayment} />
        )}

        {currentView === 'detail' && selectedPaymentId && (
          <PaymentDetail
            paymentId={selectedPaymentId}
            onBack={handleBackFromDetail}
          />
        )}
      </main>

      {/* Operational Footer */}
      <footer className="border-t border-slate-200 bg-white py-5 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-2 font-medium text-slate-600">
            <span className="font-bold text-slate-900">RecoverAI</span>
            <span>· Built for Razorpay AI Buildathon 2026 (AI Revenue Recovery Track)</span>
          </div>
          <div className="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
            <span>AI: Gemini 3.5 Flash</span>
            <span>|</span>
            <span>Policy: Deterministic Authority</span>
            <span>|</span>
            <span>Execution: SHA-256 Simulation</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
