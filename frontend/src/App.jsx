import React, { useState, useEffect } from 'react';
import { 
  BarChart2, Table, Bot, Database, HardDrive, RefreshCw, Upload, 
  Search, Filter, Sparkles, Send, FileText, CheckCircle2, ChevronRight 
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

export default function App() {
  const [activeTab, setActiveTab] = useState('explorer');
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState('sales_data.csv');
  const [tableData, setTableData] = useState({ columns: [], data: [], total_rows: 0 });
  const [searchTerm, setSearchTerm] = useState('');
  
  // AI Chat state
  const [chatQuery, setChatQuery] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { sender: 'bot', text: 'Hello! I am your BILLSzuka Gemini AI assistant. Ask me anything about your CSV datasets, sales metrics, or operational trends.' }
  ]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState('');

  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    if (selectedDataset) {
      fetchDatasetDetails(selectedDataset);
    }
  }, [selectedDataset]);

  const fetchDatasets = async () => {
    try {
      const res = await fetch('/api/datasets');
      const data = await res.json();
      setDatasets(data.datasets || []);
    } catch (err) {
      console.error('Failed to load datasets', err);
    }
  };

  const fetchDatasetDetails = async (filename) => {
    try {
      const res = await fetch(`/api/dataset/${filename}`);
      const data = await res.json();
      setTableData(data);
    } catch (err) {
      console.error('Failed to load table preview', err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setSyncStatus(`Uploaded ${data.filename}`);
      fetchDatasets();
      setSelectedDataset(data.filename);
    } catch (err) {
      setSyncStatus('Upload failed');
    }
  };

  const handleSync = async (source) => {
    setSyncStatus(`Syncing with ${source}...`);
    try {
      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_type: source }),
      });
      const data = await res.json();
      setSyncStatus(data.message);
    } catch (err) {
      setSyncStatus(`Sync failed for ${source}`);
    }
  };

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatQuery.trim()) return;

    const userMsg = chatQuery;
    setChatHistory((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setChatQuery('');
    setIsChatLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg, active_dataset: selectedDataset }),
      });
      const data = await res.json();
      setChatHistory((prev) => [...prev, { sender: 'bot', text: data.response }]);
    } catch (err) {
      setChatHistory((prev) => [...prev, { sender: 'bot', text: 'Sorry, failed to get AI analysis.' }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Filtered rows for explorer
  const filteredData = tableData.data.filter((row) =>
    Object.values(row).some((val) =>
      String(val).toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', backgroundColor: '#0f172a', color: '#f8fafc', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Header Bar */}
      <header style={{ borderBottom: '1px solid #1e293b', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#1e293b' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ backgroundColor: '#3b82f6', padding: '8px', borderRadius: '8px' }}>
            <Database size={24} color="#fff" />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>BILLSzuka Dashboard Hub</h1>
            <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Smart Data Explorer & Gemini AI Workspace</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#334155', padding: '8px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' }}>
            <Upload size={16} /> Upload CSV
            <input type="file" accept=".csv" onChange={handleFileUpload} style={{ display: 'none' }} />
          </label>
          
          <button onClick={() => handleSync('gdrive')} style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#334155', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' }}>
            <HardDrive size={16} /> Google Drive
          </button>
          
          <button onClick={() => handleSync('airtable')} style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#334155', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' }}>
            <RefreshCw size={16} /> Airtable Sync
          </button>
        </div>
      </header>

      {syncStatus && (
        <div style={{ backgroundColor: '#1e3a8a', color: '#93c5fd', padding: '8px 24px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={14} /> {syncStatus}
        </div>
      )}

      {/* Main Grid Layout */}
      <div style={{ display: 'flex', flex: 1 }}>
        
        {/* Sidebar */}
        <aside style={{ width: '260px', borderRight: '1px solid #1e293b', padding: '20px', backgroundColor: '#0f172a' }}>
          <h3 style={{ fontSize: '12px', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em', marginBottom: '12px' }}>Datasets</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '24px' }}>
            {datasets.map((d) => (
              <button
                key={d.filename}
                onClick={() => setSelectedDataset(d.filename)}
                style={{
                  textAlign: 'left',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: selectedDataset === d.filename ? '#2563eb' : '#1e293b',
                  color: '#fff',
                  cursor: 'pointer',
                  fontSize: '13px',
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center'
                }}
              >
                <span>{d.filename}</span>
                <span style={{ fontSize: '11px', opacity: 0.7 }}>{d.rows} r</span>
              </button>
            ))}
          </div>

          <h3 style={{ fontSize: '12px', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em', marginBottom: '12px' }}>Navigation</h3>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <button
              onClick={() => setActiveTab('explorer')}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', borderRadius: '6px', border: 'none',
                backgroundColor: activeTab === 'explorer' ? '#334155' : 'transparent', color: '#f8fafc', cursor: 'pointer', textAlign: 'left'
              }}
            >
              <Table size={18} /> Table Explorer
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', borderRadius: '6px', border: 'none',
                backgroundColor: activeTab === 'analytics' ? '#334155' : 'transparent', color: '#f8fafc', cursor: 'pointer', textAlign: 'left'
              }}
            >
              <BarChart2 size={18} /> Visual Analytics
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', borderRadius: '6px', border: 'none',
                backgroundColor: activeTab === 'chat' ? '#334155' : 'transparent', color: '#f8fafc', cursor: 'pointer', textAlign: 'left'
              }}
            >
              <Bot size={18} /> Gemini Assistant
            </button>
          </nav>
        </aside>

        {/* Main Content Area */}
        <main style={{ flex: 1, padding: '24px', backgroundColor: '#020617', overflowY: 'auto' }}>
          
          {/* TAB 1: TABLE EXPLORER */}
          {activeTab === 'explorer' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: '18px' }}>Active Dataset: {selectedDataset}</h2>
                  <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8' }}>Showing {filteredData.length} of {tableData.total_rows} records</p>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#1e293b', padding: '6px 12px', borderRadius: '6px' }}>
                  <Search size={16} color="#94a3b8" />
                  <input
                    type="text"
                    placeholder="Search rows..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={{ backgroundColor: 'transparent', border: 'none', color: '#fff', outline: 'none', fontSize: '14px' }}
                  />
                </div>
              </div>

              {/* Data Table */}
              <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid #1e293b', backgroundColor: '#0f172a' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#1e293b', borderBottom: '1px solid #334155' }}>
                      {tableData.columns.map((col) => (
                        <th key={col} style={{ padding: '12px 16px', color: '#cbd5e1', fontWeight: 600 }}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredData.map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #1e293b', backgroundColor: idx % 2 === 0 ? '#0f172a' : '#020617' }}>
                        {tableData.columns.map((col) => (
                          <td key={col} style={{ padding: '10px 16px', color: '#94a3b8' }}>{String(row[col])}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: VISUAL ANALYTICS */}
          {activeTab === 'analytics' && (
            <div>
              <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Visual Analytics: {selectedDataset}</h2>
              {(() => {
                // Detect numeric columns dynamically
                const numericCols = tableData.columns.filter(col =>
                  tableData.data.some(row => !isNaN(parseFloat(row[col])) && row[col] !== '')
                ).slice(0, 3);
                const xKey = tableData.columns[0] || 'id';
                const COLORS = ['#3b82f6', '#22d3ee', '#a78bfa'];
                return numericCols.length > 0 ? (
                  <div style={{ backgroundColor: '#0f172a', padding: '20px', borderRadius: '12px', border: '1px solid #1e293b', height: '400px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={tableData.data.slice(0, 50)}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey={xKey} stroke="#94a3b8" tick={{ fontSize: 11 }} />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }} />
                        <Legend />
                        {numericCols.map((col, i) => (
                          <Bar key={col} dataKey={col} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div style={{ backgroundColor: '#0f172a', padding: '40px', borderRadius: '12px', border: '1px solid #1e293b', textAlign: 'center', color: '#64748b' }}>
                    <BarChart2 size={48} style={{ margin: '0 auto 12px' }} />
                    <p>No numeric columns found in <strong>{selectedDataset}</strong>.</p>
                    <p style={{ fontSize: '13px' }}>Select a dataset with numeric fields to visualise.</p>
                  </div>
                );
              })()}
            </div>
          )}


          {/* TAB 3: GEMINI CHAT ASSISTANT */}
          {activeTab === 'chat' && (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', maxWidth: '800px', margin: '0 auto' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Sparkles color="#3b82f6" />
                <h2 style={{ margin: 0, fontSize: '18px' }}>Chat with your Data (Gemini AI)</h2>
              </div>

              {/* Chat Window */}
              <div style={{ flex: 1, backgroundColor: '#0f172a', borderRadius: '12px', border: '1px solid #1e293b', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', minHeight: '400px', overflowY: 'auto' }}>
                {chatHistory.map((msg, idx) => (
                  <div
                    key={idx}
                    style={{
                      alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                      backgroundColor: msg.sender === 'user' ? '#2563eb' : '#1e293b',
                      color: '#fff',
                      padding: '12px 16px',
                      borderRadius: '12px',
                      maxWidth: '80%',
                      fontSize: '14px',
                      whiteSpace: 'pre-wrap'
                    }}
                  >
                    {msg.text}
                  </div>
                ))}
                {isChatLoading && (
                  <div style={{ alignSelf: 'flex-start', color: '#94a3b8', fontSize: '13px' }}>
                    Gemini is processing your dataset query...
                  </div>
                )}
              </div>

              {/* Input Form */}
              <form onSubmit={handleSendChat} style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                <input
                  type="text"
                  placeholder="Ask a question about sales revenue, region totals..."
                  value={chatQuery}
                  onChange={(e) => setChatQuery(e.target.value)}
                  style={{ flex: 1, backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '12px 16px', color: '#fff', outline: 'none' }}
                />
                <button
                  type="submit"
                  style={{ backgroundColor: '#2563eb', color: '#fff', border: 'none', padding: '0 20px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
