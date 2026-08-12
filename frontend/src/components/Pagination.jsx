import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const Pagination = ({
  currentPage = 1,
  totalPages = 1,
  totalItems = 0,
  pageSize = 10,
  onPageChange,
  onPageSizeChange
}) => {
  if (totalItems === 0) return null;

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  // Generate visible page numbers array
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    let start = Math.max(1, currentPage - 2);
    let end = Math.min(totalPages, start + maxVisible - 1);

    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-dark-border text-xs text-slate-400">
      {/* Information Counter & Page Size Selector */}
      <div className="flex items-center space-x-4">
        <span>
          Showing <strong className="text-slate-200">{startItem}</strong> to{' '}
          <strong className="text-slate-200">{endItem}</strong> of{' '}
          <strong className="text-slate-200">{totalItems.toLocaleString()}</strong> records
        </span>

        {onPageSizeChange && (
          <div className="flex items-center space-x-1.5">
            <label htmlFor="page-size-select" className="text-dark-muted">Rows:</label>
            <select
              id="page-size-select"
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="bg-slate-900 border border-dark-border rounded-lg px-2 py-1 text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center space-x-1.5">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          aria-label="Previous Page"
          className="p-2 rounded-xl bg-slate-900 border border-dark-border text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {getPageNumbers().map((page) => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`px-3 py-1.5 rounded-xl font-mono text-xs font-bold transition-all focus-visible:ring-2 focus-visible:ring-blue-500 ${
              currentPage === page
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20 border border-blue-500/30'
                : 'bg-slate-900 border border-dark-border text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            {page}
          </button>
        ))}

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages || totalPages === 0}
          aria-label="Next Page"
          className="p-2 rounded-xl bg-slate-900 border border-dark-border text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default Pagination;
