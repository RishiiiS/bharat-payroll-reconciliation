import React from 'react';
import { LayoutDashboard, FileText, BarChart2, Calendar, Users, ShieldAlert } from 'lucide-react';

const Sidebar = () => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 hidden md:flex flex-col h-full shrink-0">
      <div className="p-6 border-b border-slate-100 flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white font-bold text-lg">P</div>
        <h1 className="text-lg font-bold text-slate-800 tracking-tight">Payroll Recon</h1>
      </div>
      
      <div className="flex-1 py-6 flex flex-col gap-8">
        <div>
          <h2 className="px-6 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Main Menu</h2>
          <nav className="flex flex-col gap-1 px-3">
            <a href="#" className="flex items-center gap-3 px-3 py-2.5 bg-blue-50 text-blue-700 rounded-lg font-medium transition-colors">
              <LayoutDashboard size={18} />
              <span>Overview</span>
            </a>
            <a href="#" className="flex items-center gap-3 px-3 py-2.5 text-slate-600 hover:bg-slate-50 rounded-lg font-medium transition-colors">
              <FileText size={18} />
              <span>Reconcile</span>
            </a>
            <a href="#" className="flex items-center gap-3 px-3 py-2.5 text-slate-600 hover:bg-slate-50 rounded-lg font-medium transition-colors">
              <BarChart2 size={18} />
              <span>Reports</span>
            </a>
          </nav>
        </div>
        
        <div>
          <h2 className="px-6 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Admin Portal</h2>
          <nav className="flex flex-col gap-1 px-3">
            <a href="#" className="flex items-center gap-3 px-3 py-2.5 text-slate-600 hover:bg-slate-50 rounded-lg font-medium transition-colors">
              <Calendar size={18} />
              <span>Payroll Cycles</span>
            </a>
            <a href="#" className="flex items-center gap-3 px-3 py-2.5 text-slate-600 hover:bg-slate-50 rounded-lg font-medium transition-colors">
              <Users size={18} />
              <span>Employee Directory</span>
            </a>
            <a href="#" className="flex items-center gap-3 px-3 py-2.5 text-slate-600 hover:bg-slate-50 rounded-lg font-medium transition-colors">
              <ShieldAlert size={18} />
              <span>Audit Logs</span>
            </a>
          </nav>
        </div>
      </div>
      
      <div className="p-4 border-t border-slate-100 text-xs text-slate-400">
        <p className="font-medium">Admin Portal v2.4.0</p>
      </div>
    </aside>
  );
};

export default Sidebar;
