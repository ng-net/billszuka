'use client';

import { useState, useEffect } from 'react';
import { Database, Sparkles, RefreshCw, HardDrive, Table, BarChart2 } from 'lucide-react';

export default function Home() {
  const [data, setData] = useState<{ metrics: any[]; aiSummary: string }>({ metrics: [], aiSummary: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/dashboard')
      .then((res) => res.json())
      .then((resData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Database className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold">BILLSzuka Next.js Architecture Hub</h1>
            <p className="text-xs text-slate-400">Vercel + Cloudflare Ready | Airtable & Gemini Pro Powered</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-8 max-w-6xl mx-auto space-y-8">
        
        {/* Gemini AI Summary Card */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
          <div className="flex items-center gap-2 mb-4 text-blue-400 font-semibold text-lg">
            <Sparkles className="w-5 h-5" />
            <span>Gemini Pro AI Insights</span>
          </div>
          {loading ? (
            <p className="text-slate-400 text-sm animate-pulse">Running Gemini reasoning model against dashboard metrics...</p>
          ) : (
            <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-line bg-slate-950/50 p-4 rounded-lg border border-slate-800">
              {data.aiSummary}
            </div>
          )}
        </section>

        {/* Dashboard Metrics Table */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Table className="w-5 h-5 text-slate-400" />
              Synced Data Metrics
            </h2>
            <span className="text-xs bg-slate-800 text-slate-300 px-3 py-1 rounded-full">
              {data.metrics.length} Records Loaded
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800 text-slate-300 uppercase text-xs">
                <tr>
                  <th className="p-3">Customer</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Amount (USD)</th>
                  <th className="p-3">Region</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-950">
                {data.metrics.map((m: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-900/50 transition">
                    <td className="p-3 font-medium text-white">{m.Customer || m.Customer_Name || 'N/A'}</td>
                    <td className="p-3 text-slate-400">{m.Category || 'N/A'}</td>
                    <td className="p-3 text-emerald-400 font-mono">${(m.Amount_USD || 0).toLocaleString()}</td>
                    <td className="p-3 text-slate-400">{m.Region || 'N/A'}</td>
                    <td className="p-3">
                      <span className="bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 text-xs rounded-full">
                        {m.Status || 'Completed'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

      </main>
    </div>
  );
}
