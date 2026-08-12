import React from 'react';

export const MetricCardSkeleton = () => (
  <div className="glass-panel p-6 rounded-2xl flex items-center space-x-5 animate-pulse">
    <div className="w-14 h-14 rounded-xl bg-slate-800/80" />
    <div className="space-y-2 flex-1">
      <div className="h-3 bg-slate-800/80 rounded w-1/2" />
      <div className="h-7 bg-slate-800/80 rounded w-3/4" />
    </div>
  </div>
);

export const TableRowSkeleton = ({ columns = 5 }) => (
  <tr className="border-b border-dark-border/40 animate-pulse">
    {Array.from({ length: columns }).map((_, idx) => (
      <td key={idx} className="py-4 px-4">
        <div className="h-4 bg-slate-800/80 rounded w-full max-w-[120px]" />
      </td>
    ))}
  </tr>
);

export const ChartSkeleton = () => (
  <div className="w-full h-full min-h-[220px] bg-slate-900/40 rounded-2xl p-6 flex flex-col justify-between animate-pulse border border-dark-border/40">
    <div className="flex justify-between items-center">
      <div className="h-4 bg-slate-800 rounded w-1/4" />
      <div className="h-4 bg-slate-800 rounded w-1/6" />
    </div>
    <div className="flex items-end justify-between space-x-4 h-36 pt-6">
      <div className="w-1/6 bg-slate-800/60 rounded-t h-[40%]" />
      <div className="w-1/6 bg-slate-800/60 rounded-t h-[70%]" />
      <div className="w-1/6 bg-slate-800/60 rounded-t h-[55%]" />
      <div className="w-1/6 bg-slate-800/60 rounded-t h-[90%]" />
      <div className="w-1/6 bg-slate-800/60 rounded-t h-[65%]" />
    </div>
  </div>
);
