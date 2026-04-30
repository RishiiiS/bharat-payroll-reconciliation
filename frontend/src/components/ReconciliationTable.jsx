import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronDown, ChevronUp, AlertTriangle, AlertCircle, Loader2 } from 'lucide-react';

const ShiftDetails = ({ workerId }) => {
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchShifts = async () => {
      try {
        const response = await axios.get(`http://127.0.0.1:8000/worker/${workerId}/shifts`);
        if (response.data.error) {
          setError(response.data.error);
        } else {
          setShifts(response.data);
        }
      } catch (err) {
        setError("Failed to fetch shift details.");
      } finally {
        setLoading(false);
      }
    };
    fetchShifts();
  }, [workerId]);

  if (loading) {
    return <div className="p-4 flex items-center gap-2 text-slate-500"><Loader2 className="animate-spin" size={16} /> Loading shift details...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500 text-sm flex items-center gap-2"><AlertCircle size={16} /> {error}</div>;
  }

  if (shifts.length === 0) {
    return <div className="p-4 text-slate-500 text-sm">No shift details found for this worker.</div>;
  }

  const formatCurrency = (val) => `₹${Number(val).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2})}`;

  return (
    <div className="mt-4 border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
      <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
        Shift-Level Expected Pay Breakdown
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="bg-slate-50 text-slate-500 border-b border-slate-100">
            <tr>
              <th className="px-4 py-3 font-semibold">Date</th>
              <th className="px-4 py-3 font-semibold text-right">Hours Worked</th>
              <th className="px-4 py-3 font-semibold text-right">Hourly Rate</th>
              <th className="px-4 py-3 font-semibold text-right">Expected Pay</th>
              <th className="px-4 py-3 font-semibold">Flags</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {shifts.map((shift, i) => {
              const hasFlags = shift.needs_manual_review === "True" || shift.needs_manual_review === true;
              // Handle Pandas timestamp parsing safely
              const dateStr = shift.work_date ? new Date(shift.work_date).toLocaleDateString() : 'Unknown';
              return (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-medium">{dateStr}</td>
                  <td className="px-4 py-2.5 text-right">{Number(shift.hours_worked).toFixed(1)}</td>
                  <td className="px-4 py-2.5 text-right">{formatCurrency(shift.hourly_rate)}</td>
                  <td className="px-4 py-2.5 text-right font-medium text-slate-900">{formatCurrency(shift.expected_pay)}</td>
                  <td className="px-4 py-2.5">
                    {hasFlags && (
                      <span className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-100 px-2 py-1 rounded">
                        <AlertTriangle size={12} />
                        {shift.review_reason || 'Flagged'}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const ReconciliationTable = ({ data }) => {
  const [expandedRows, setExpandedRows] = useState(new Set());

  const toggleRow = (id) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const formatCurrency = (val) => `₹${Number(val).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2})}`;

  const getStatus = (diff) => {
    if (diff > 0) return { label: 'UNDERPAID', color: 'text-red-700 bg-red-100' };
    if (diff < 0) return { label: 'OVERPAID', color: 'text-amber-700 bg-amber-100' };
    return { label: 'MATCHED', color: 'text-emerald-700 bg-emerald-100' };
  };

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center text-slate-500">
        No workers found matching your filters.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="text-xs uppercase bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
            <tr>
              <th className="px-6 py-4">Worker ID</th>
              <th className="px-6 py-4">Worker Name</th>
              <th className="px-6 py-4">Expected (₹)</th>
              <th className="px-6 py-4">Actual (₹)</th>
              <th className="px-6 py-4">Difference</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.map((row) => {
              const isExpanded = expandedRows.has(row.worker_id);
              const status = getStatus(row.difference);
              const needsReview = row.needs_manual_review === "True" || row.needs_manual_review === true;

              return (
                <React.Fragment key={row.worker_id}>
                  {/* Main Row */}
                  <tr className={`hover:bg-slate-50 transition-colors ${isExpanded ? 'bg-slate-50' : ''}`}>
                    <td className="px-6 py-4 font-medium text-slate-900 flex items-center gap-2">
                      {row.worker_id}
                      {needsReview && <AlertTriangle size={16} className="text-red-500" title="Needs Manual Review" />}
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-700">{row.name || 'Unknown'}</td>
                    <td className="px-6 py-4">{formatCurrency(row.trusted_expected_pay)}</td>
                    <td className="px-6 py-4 font-medium">{formatCurrency(row.total_actual_pay)}</td>
                    <td className={`px-6 py-4 font-semibold ${row.difference > 0 ? 'text-red-600' : row.difference < 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                      {row.difference > 0 ? '+' : ''}{formatCurrency(row.difference)}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${status.color}`}>
                        {status.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => toggleRow(row.worker_id)}
                        className="text-blue-600 hover:text-blue-800 font-medium text-sm flex items-center gap-1 justify-end w-full"
                      >
                        View Details {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                    </td>
                  </tr>

                  {/* Expanded Details Row */}
                  {isExpanded && (
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <td colSpan="7" className="px-6 pb-6 pt-2">
                        <div className="flex flex-col gap-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-white rounded-lg border border-slate-200 shadow-sm">
                            <div>
                              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Review Reason</h4>
                              <p className="text-slate-800 text-sm">
                                {row.review_reason || "No manual review reason specified."}
                              </p>
                            </div>
                            <div>
                              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Missing Shifts</h4>
                              <div className="flex items-center gap-3">
                                <span className="text-2xl font-bold text-red-600">{row.missing_shifts || 0}</span>
                                {row.missing_shifts > 0 && (
                                  <button className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded text-xs font-semibold transition-colors">
                                    Correct Manually
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          {/* Shift Level Breakdown Details */}
                          <ShiftDetails workerId={row.worker_id} />
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ReconciliationTable;
