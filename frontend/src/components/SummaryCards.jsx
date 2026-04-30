import React from 'react';
import { Users, AlertTriangle, AlertCircle, IndianRupee } from 'lucide-react';

const SummaryCards = ({ data }) => {
  const totalWorkers = data.length;
  
  // Logic: difference > 0 means expected > actual, so they are underpaid
  const underpaid = data.filter(d => d.difference > 0);
  const overpaid = data.filter(d => d.difference < 0);
  
  // Discrepancy is actual total discrepancy (sum of all differences)
  // or sum of absolute differences to show total scale of error. Let's show net discrepancy
  const totalDiscrepancy = Math.abs(data.reduce((sum, item) => sum + item.difference, 0));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {/* Total Workers */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-sm font-semibold text-slate-500">Total Workers</h3>
          <div className="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center text-slate-400">
            <Users size={16} />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-slate-800">{totalWorkers.toLocaleString()}</span>
        </div>
      </div>

      {/* Underpaid Workers */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100 border-l-4 border-l-red-500 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-sm font-semibold text-slate-500">Underpaid Workers</h3>
          <div className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center text-red-500">
            <AlertTriangle size={16} />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-slate-800">{underpaid.length}</span>
          <span className="text-xs font-semibold text-red-500 bg-red-50 px-2 py-0.5 rounded">Action Required</span>
        </div>
      </div>

      {/* Overpaid Workers */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100 border-l-4 border-l-amber-400 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-sm font-semibold text-slate-500">Overpaid Workers</h3>
          <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center text-amber-500">
            <AlertCircle size={16} />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-slate-800">{overpaid.length}</span>
          <span className="text-xs font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded">To Review</span>
        </div>
      </div>

      {/* Total Discrepancy */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-sm font-semibold text-slate-500">Net Discrepancy</h3>
          <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center text-blue-500">
            <IndianRupee size={16} />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-slate-800">₹{totalDiscrepancy.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}</span>
        </div>
      </div>
    </div>
  );
};

export default SummaryCards;
