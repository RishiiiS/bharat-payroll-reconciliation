import React, { useMemo } from 'react';

const InsightCard = ({ title, value, subtitle, colorHint }) => {
  const borderColors = {
    red: 'border-l-red-500',
    yellow: 'border-l-amber-400',
    green: 'border-l-emerald-500',
    neutral: 'border-l-slate-200'
  };
  
  const textColors = {
    red: 'text-red-600',
    yellow: 'text-amber-600',
    green: 'text-emerald-600',
    neutral: 'text-slate-800'
  };

  return (
    <div className={`bg-white rounded-lg p-4 shadow-sm border border-slate-100 border-l-4 ${borderColors[colorHint] || borderColors.neutral} flex flex-col justify-between`}>
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{title}</h3>
      <div className={`text-2xl font-bold mb-1 ${textColors[colorHint] || textColors.neutral}`}>
        {value}
      </div>
      <p className="text-xs text-slate-400">{subtitle}</p>
    </div>
  );
};

const DetailedInsights = ({ data, shiftDataRaw, bankDataRaw }) => {
  const stats = useMemo(() => {
    const totalShifts = shiftDataRaw ? shiftDataRaw.trim().split('\n').length - 1 : 0;
    const totalPayments = bankDataRaw ? bankDataRaw.trim().split('\n').length - 1 : 0;
    
    const missingShifts = Math.max(0, totalShifts - totalPayments);
    const percentMissing = totalShifts > 0 ? ((missingShifts / totalShifts) * 100).toFixed(1) : 0;
    
    let totalExpected = 0;
    let totalActual = 0;
    let underpaymentSum = 0;
    let overpaymentSum = 0;
    
    if (data && data.length > 0) {
      data.forEach(row => {
        totalExpected += (Number(row.trusted_expected_pay) || 0);
        totalActual += (Number(row.total_actual_pay) || 0);
        
        const diff = Number(row.difference) || 0;
        // Apply tolerance: differences < 100 are considered rounding noise
        if (diff > 100) underpaymentSum += diff;
        if (diff < -100) overpaymentSum += Math.abs(diff);
      });
    }
    
    return {
      totalShifts,
      totalPayments,
      missingShifts,
      percentMissing,
      totalExpected,
      totalActual,
      underpaymentSum,
      overpaymentSum
    };
  }, [data, shiftDataRaw, bankDataRaw]);

  const formatCurrency = (val) => `₹${Number(val).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2})}`;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <InsightCard 
        title="Total Expected Pay" 
        value={formatCurrency(stats.totalExpected)} 
        subtitle="Computed wages"
        colorHint="neutral"
      />
      <InsightCard 
        title="Total Actual Pay" 
        value={formatCurrency(stats.totalActual)} 
        subtitle="Paid via bank"
        colorHint="neutral"
      />
      <InsightCard 
        title="Total Underpayment" 
        value={formatCurrency(stats.underpaymentSum)} 
        subtitle="Amount owed to workers"
        colorHint="red"
      />
      <InsightCard 
        title="Total Overpayment" 
        value={formatCurrency(stats.overpaymentSum)} 
        subtitle="Excess paid amount"
        colorHint="yellow"
      />
    </div>
  );
};

export default DetailedInsights;
