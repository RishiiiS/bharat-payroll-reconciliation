import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronDown, ChevronUp, AlertTriangle, AlertCircle, Loader2 } from 'lucide-react';

const ShiftDetails = ({ workerId, missingCount = 0, difference = 0 }) => {
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

  // 1. Identify explicitly flagged missing shifts
  let explicitMissing = shifts.filter(s => {
    const expected = Number(s.expected_pay) || 0;
    if (expected <= 0) return false;
    
    const rate = Number(s.hourly_rate) || 0;
    const reason = (s.review_reason || "").toLowerCase();
    
    return (
      rate === 0 ||
      reason.includes("missing payment") ||
      reason.includes("no payment match")
    );
  });

  // 2. If we need more to match the worker's total missing count, pick the most recent unflagged shifts
  if (explicitMissing.length < missingCount && missingCount > 0) {
    const remainingNeeded = missingCount - explicitMissing.length;
    const unflagged = shifts.filter(s => !explicitMissing.includes(s));
    // Sort unflagged by date descending (newest first)
    const sortedUnflagged = [...unflagged].sort((a, b) => new Date(b.work_date) - new Date(a.work_date));
    explicitMissing = [...explicitMissing, ...sortedUnflagged.slice(0, remainingNeeded)];
  }

  const missingShifts = explicitMissing;
  const missingShiftIds = new Set(missingShifts.map(s => s.log_id || s.work_date));

  const totalUnpaid = missingShifts.reduce((sum, s) => sum + (Number(s.expected_pay) || 0), 0);
  
  const TOLERANCE = 100;
  const absDifference = Math.abs(difference);
  const isRoundingDiff = difference !== 0 && absDifference < TOLERANCE;
  const isUnderpaid = difference > 0 && !isRoundingDiff;
  const isOverpaid = difference < 0 && !isRoundingDiff;
  const excessAmount = absDifference;

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
              const dateStr = shift.work_date ? new Date(shift.work_date).toLocaleDateString() : 'Unknown';
              
              const expected = Number(shift.expected_pay) || 0;
              const isMissing = missingShiftIds.has(shift.log_id || shift.work_date);

              return (
                <tr key={i} className={`transition-colors ${isMissing ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-slate-50'}`}>
                  <td className="px-4 py-2.5 font-medium flex items-center gap-2">
                    {dateStr}
                    {isMissing && <AlertCircle size={14} className="text-red-500" title="Shift was unpaid" />}
                  </td>
                  <td className="px-4 py-2.5 text-right">{Number(shift.hours_worked).toFixed(1)}</td>
                  <td className="px-4 py-2.5 text-right">{formatCurrency(shift.hourly_rate)}</td>
                  <td className={`px-4 py-2.5 text-right font-medium ${isMissing ? 'text-red-700' : 'text-slate-900'}`}>{formatCurrency(shift.expected_pay)}</td>
                  <td className="px-4 py-2.5">
                    {hasFlags && (
                      <span 
                        title={shift.review_reason === 'overlapping wage rates' ? 'Multiple wage rates matched this shift' : shift.review_reason}
                        className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-100 px-2 py-1 rounded cursor-help"
                      >
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

      {/* MISSING SHIFTS SECTION - ONLY FOR UNDERPAID */}
      {isUnderpaid && missingShifts.length > 0 && (
        <div className="border-t border-slate-200 bg-slate-50 p-4">
          <p className="text-sm text-slate-500 mb-4 italic border-l-2 border-slate-300 pl-3">
            These shifts have expected earnings but no corresponding bank transfer record.
          </p>
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
            MISSING SHIFTS (UNPAID)
          </h4>
          <div className="mb-3 text-sm text-slate-600">
            Missing Shifts: <span className="font-bold text-slate-900">{missingShifts.length}</span> (₹{totalUnpaid.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2})} unpaid)
          </div>
          <div className="bg-white rounded border border-red-100 overflow-hidden shadow-sm max-w-xl">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-slate-500 border-b border-slate-100 text-xs uppercase">
                <tr>
                  <th className="px-4 py-2 font-semibold">Date</th>
                  <th className="px-4 py-2 font-semibold text-right border-l border-slate-100">Expected Pay</th>
                  <th className="px-4 py-2 font-semibold text-right border-l border-slate-100">Payment Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {missingShifts.map((m, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-4 py-2">{m.work_date ? new Date(m.work_date).toLocaleDateString() : 'Unknown Date'}</td>
                    <td className="px-4 py-2 text-right font-medium text-slate-900 border-l border-slate-100">
                      ₹{Number(m.expected_pay || 0).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2})}
                    </td>
                    <td className="px-4 py-2 text-right border-l border-slate-100">
                      <span 
                        className="text-slate-500 italic text-xs font-medium cursor-help bg-slate-100 px-2 py-0.5 rounded border border-slate-200"
                        title="No matching bank transfer found for this shift"
                      >
                        No Matching Payment
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* OVERPAID SECTION - ONLY FOR OVERPAID */}
      {isOverpaid && (
        <div className="border-t border-slate-200 bg-amber-50 p-4">
          <h4 className="text-xs font-bold text-amber-700 uppercase tracking-wider mb-3">
            UNMAPPED PAYMENTS (EXCESS)
          </h4>
          <div className="mb-2 text-sm text-amber-900 font-medium">
            Excess Amount: <span className="font-bold text-amber-700 text-lg ml-1">₹{excessAmount.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2})}</span>
          </div>
          <p className="text-sm text-amber-700 italic opacity-80 mt-2">
            These payments could not be mapped to any recorded shifts.
          </p>
        </div>
      )}

      {/* ROUNDING DIFFERENCE SECTION - ONLY FOR SMALL DIFFERENCES */}
      {isRoundingDiff && (
        <div className="border-t border-slate-200 bg-slate-50 p-4">
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
            ROUNDING DIFFERENCE
          </h4>
          <div className="mb-2 text-sm text-slate-700 font-medium">
            Difference: <span className="font-bold text-slate-800 text-lg ml-1">₹{excessAmount.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2})}</span>
          </div>
          <p className="text-sm text-slate-500 italic mt-2 border-l-2 border-slate-300 pl-3">
            This difference is within tolerance and likely caused by rounding or precision mismatches.
          </p>
        </div>
      )}
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
    const TOLERANCE = 100;
    if (Math.abs(diff) < TOLERANCE) return { label: 'MATCHED', color: 'text-emerald-700 bg-emerald-100', rowBg: 'bg-emerald-50 hover:bg-emerald-100/80' };
    if (diff > 0) return { label: 'UNDERPAID', color: 'text-red-700 bg-red-100', rowBg: 'bg-red-50 hover:bg-red-100/80' };
    return { label: 'OVERPAID', color: 'text-amber-700 bg-amber-100', rowBg: 'bg-amber-50 hover:bg-amber-100/80' };
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
              <th className="px-6 py-4 text-right">Expected (₹)</th>
              <th className="px-6 py-4 text-right">Actual (₹)</th>
              <th className="px-6 py-4 text-right">Difference</th>
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
                  <tr className={`transition-colors border-b border-slate-100 ${isExpanded ? 'shadow-inner' : ''} ${status.rowBg}`}>
                    <td className="px-6 py-4 font-medium text-slate-900 flex items-center gap-2">
                      {row.worker_id}
                      {needsReview && <AlertTriangle size={16} className="text-red-500" title="Needs Manual Review" />}
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-700">{row.name || 'Unknown'}</td>
                    <td className="px-6 py-4 text-right">{formatCurrency(row.trusted_expected_pay)}</td>
                    <td className="px-6 py-4 font-medium text-right">{formatCurrency(row.total_actual_pay)}</td>
                    <td className={`px-6 py-4 font-semibold text-right ${row.difference > 0 ? 'text-red-600' : row.difference < 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
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
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-4 bg-white rounded-lg border border-slate-200 shadow-sm">
                            <div>
                              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Review Reason</h4>
                              <p className="text-slate-800 text-sm">
                                {row.review_reason || "No manual review reason specified."}
                              </p>
                            </div>
                            <div>
                              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Shift Statistics</h4>
                              <div className="flex flex-col gap-1 text-sm text-slate-600">
                                <div className="flex justify-between w-32"><span>Total Shifts:</span> <span className="font-semibold text-slate-900">{row.num_shifts || 0}</span></div>
                                <div className="flex justify-between w-32"><span>Paid Shifts:</span> <span className="font-semibold text-slate-900">{row.num_payments || 0}</span></div>
                                <div className="flex justify-between w-32"><span>Missing Shifts:</span> <span className={`font-semibold ${row.missing_shifts > 0 ? 'text-red-600' : 'text-slate-900'}`}>{row.missing_shifts || 0}</span></div>
                              </div>
                            </div>
                            <div>
                              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Action Required</h4>
                              <div className="flex items-center mt-2">
                                {row.missing_shifts > 0 && (
                                  <button className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded text-xs font-semibold transition-colors">
                                    Correct Manually
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          {/* Shift Level Breakdown Details */}
                          <ShiftDetails workerId={row.worker_id} missingCount={row.missing_shifts || 0} difference={row.difference} />
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
