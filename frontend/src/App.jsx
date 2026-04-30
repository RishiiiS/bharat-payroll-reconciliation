import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Download, Loader2, AlertCircle } from 'lucide-react';
import Sidebar from './components/Sidebar';
import SummaryCards from './components/SummaryCards';
import FilterRow from './components/FilterRow';
import ReconciliationTable from './components/ReconciliationTable';

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter States
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [showOnlyIssues, setShowOnlyIssues] = useState(true); // Default to true

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:8000/reconciliation');
        if (response.data.error) {
          setError(response.data.error);
        } else {
          setData(response.data);
        }
      } catch (err) {
        setError("Failed to fetch data. Ensure the Python backend is running.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredData = useMemo(() => {
    return data.filter(row => {
      // 1. Search term
      if (searchTerm && !row.worker_id.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // 2. Status Dropdown
      if (statusFilter !== 'All') {
        if (statusFilter === 'Underpaid' && row.difference <= 0) return false;
        if (statusFilter === 'Overpaid' && row.difference >= 0) return false;
        if (statusFilter === 'Matched' && Math.abs(row.difference) > 100) return false;
        // Strict matched = 0, but reference uses abs(diff) <= 100 or diff == 0. 
        // For visual, diff < 0 is Underpaid, diff > 0 is Overpaid, so diff == 0 is matched
        if (statusFilter === 'Matched' && row.difference !== 0) return false;
      }

      // 3. Show only issues
      if (showOnlyIssues) {
        const needsReview = row.needs_manual_review === "True" || row.needs_manual_review === true;
        if (!needsReview && row.difference === 0) {
          return false;
        }
      }

      return true;
    }).sort((a, b) => {
      // Sort by highest absolute discrepancy
      return Math.abs(b.difference) - Math.abs(a.difference);
    });
  }, [data, searchTerm, statusFilter, showOnlyIssues]);

  const handleExportCSV = () => {
    if (data.length === 0) return;
    const headers = ['worker_id', 'name', 'trusted_expected_pay', 'total_actual_pay', 'difference', 'classification', 'needs_manual_review', 'review_reason'];
    const csvContent = "data:text/csv;charset=utf-8," 
      + headers.join(',') + "\n"
      + data.map(row => {
          return headers.map(header => {
            const val = row[header] === null || row[header] === undefined ? "" : row[header];
            // Escape quotes and wrap in quotes to handle commas
            return `"${String(val).replace(/"/g, '""')}"`;
          }).join(',');
      }).join("\n");
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "reconciliation_results.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="animate-spin text-blue-600" size={48} />
          <p className="text-slate-500 font-medium text-lg">Loading reconciliation data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
        <div className="bg-white p-8 rounded-xl shadow-lg border border-red-100 max-w-md w-full flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center text-red-500 mb-6">
            <AlertCircle size={32} />
          </div>
          <h2 className="text-xl font-bold text-slate-800 mb-2">Connection Error</h2>
          <p className="text-slate-600 mb-6">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="w-full bg-slate-800 text-white font-medium py-3 rounded-lg hover:bg-slate-900 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col">
        {/* Header Section */}
        <header className="bg-white border-b border-slate-200 px-6 py-8 md:px-10 shrink-0">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 max-w-7xl mx-auto">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Payroll Reconciliation Dashboard</h1>
              <p className="text-slate-500 mt-1">Reviewing cycle for Period Oct 01 - Oct 15, 2023</p>
            </div>
            
            <div className="flex gap-3 w-full md:w-auto mt-4 md:mt-0">
              <button 
                onClick={handleExportCSV}
                className="flex-1 md:flex-none flex items-center justify-center gap-2 px-5 py-2.5 bg-white border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
              >
                <Download size={18} />
                Export CSV
              </button>
            </div>
          </div>
        </header>

        {/* Content Section */}
        <div className="p-6 md:p-10 max-w-7xl mx-auto w-full flex-1">
          {/* Insight Banner */}
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="text-blue-500 shrink-0 mt-0.5" size={20} />
            <p className="text-blue-800 text-sm">
              <span className="font-semibold">Insight:</span> ~12% of shifts are not converted into payments, causing most discrepancies.
            </p>
          </div>
          <SummaryCards data={data} />
          
          <FilterRow 
            searchTerm={searchTerm} 
            setSearchTerm={setSearchTerm}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            showOnlyIssues={showOnlyIssues}
            setShowOnlyIssues={setShowOnlyIssues}
          />

          <div className="mb-4 flex items-center justify-between text-sm text-slate-500">
            <p>Showing {filteredData.length} of {data.length} workers</p>
          </div>

          <ReconciliationTable data={filteredData} />
          
        </div>
      </main>
    </div>
  );
}

export default App;
