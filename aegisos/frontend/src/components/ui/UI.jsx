import React from 'react';

// ===== CARD =====
export const Card = ({ children, className = '', hover = false, ...props }) => (
  <div className={`bg-[#111113] border border-[#1f1f23] rounded-lg ${hover ? 'transition-all hover:border-[#2a2a2e] hover:bg-[#161618]' : ''} ${className}`} {...props}>
    {children}
  </div>
);

// ===== STAT CARD =====
export const StatCard = ({ icon: Icon, label, value, color = 'text-white', sublabel }) => (
  <div className="bg-[#111113] border border-[#1f1f23] rounded-lg p-4 transition-all hover:border-[#2a2a2e]">
    <div className="flex items-center justify-between mb-2">
      {Icon && <div className="w-9 h-9 rounded-lg bg-teal-400/10 flex items-center justify-center">
        <Icon className="w-5 h-5 text-teal-400" />
      </div>}
    </div>
    <div className={`text-2xl font-bold ${color}`}>{value}</div>
    <div className="text-xs text-gray-500 mt-1">{label}</div>
    {sublabel && <div className="text-[10px] text-gray-600 mt-0.5">{sublabel}</div>}
  </div>
);

// ===== BUTTON =====
export const Button = ({ children, variant = 'primary', size = 'md', className = '', ...props }) => {
  const variants = {
    primary: 'bg-teal-400 text-[#0a0a0b] hover:bg-teal-300 font-medium',
    secondary: 'border border-[#2a2a2e] text-gray-300 hover:bg-[#161618] hover:border-[#3a3a3e]',
    ghost: 'text-gray-400 hover:text-white hover:bg-white/5',
    danger: 'bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20',
    success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20',
  };
  const sizes = {
    sm: 'px-3 py-1.5 text-xs rounded-md',
    md: 'px-4 py-2 text-sm rounded-lg',
    lg: 'px-6 py-3 text-sm rounded-lg',
  };
  return (
    <button className={`inline-flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  );
};

// ===== BADGE =====
export const Badge = ({ children, variant = 'default', size = 'sm' }) => {
  const variants = {
    default: 'bg-white/5 text-gray-400 border-white/10',
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    danger: 'bg-red-500/10 text-red-400 border-red-500/20',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    teal: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  };
  const sizes = { sm: 'px-2 py-0.5 text-[10px]', md: 'px-2.5 py-1 text-xs' };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border font-medium ${variants[variant]} ${sizes[size]}`}>
      {children}
    </span>
  );
};

// ===== STATUS DOT =====
export const StatusDot = ({ status = 'online' }) => {
  const colors = { online: 'bg-emerald-400', warning: 'bg-amber-400', error: 'bg-red-400', offline: 'bg-gray-600' };
  return (
    <span className="relative flex items-center justify-center">
      <span className={`w-2 h-2 rounded-full ${colors[status] || colors.offline} ${status === 'online' ? 'animate-pulse' : ''}`}></span>
    </span>
  );
};

// ===== INPUT =====
export const Input = ({ label, error, className = '', ...props }) => (
  <div className="w-full">
    {label && <label className="block text-xs text-gray-400 mb-1.5">{label}</label>}
    <input
      className={`w-full bg-[#0a0a0b] border border-[#1f1f23] rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-teal-400/50 focus:ring-1 focus:ring-teal-400/20 transition-all ${error ? 'border-red-500/50' : ''} ${className}`}
      {...props}
    />
    {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
  </div>
);

// ===== TABLE =====
export const Table = ({ columns, data, emptyMessage = 'No data' }) => (
  <div className="overflow-x-auto">
    <table className="w-full">
      <thead>
        <tr className="border-b border-[#1f1f23]">
          {columns.map((col, i) => (
            <th key={i} className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-4 py-3">
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.length === 0 ? (
          <tr><td colSpan={columns.length} className="text-center text-gray-600 py-8 text-sm">{emptyMessage}</td></tr>
        ) : data.map((row, i) => (
          <tr key={i} className="border-b border-[#1f1f23] hover:bg-[#161618] transition-colors">
            {columns.map((col, j) => (
              <td key={j} className="px-4 py-3 text-sm text-gray-300">
                {col.render ? col.render(row) : row[col.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// ===== TABS =====
export const Tabs = ({ tabs, active, onChange }) => (
  <div className="flex items-center gap-1 border-b border-[#1f1f23] overflow-x-auto">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        onClick={() => onChange(tab.id)}
        className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
          active === tab.id
            ? 'border-teal-400 text-white'
            : 'border-transparent text-gray-500 hover:text-gray-300'
        }`}
      >
        {tab.label}
        {tab.count !== undefined && <span className="ml-2 text-xs text-gray-600">{tab.count}</span>}
      </button>
    ))}
  </div>
);

// ===== PAGE HEADER =====
export const PageHeader = ({ title, subtitle, actions, icon: Icon }) => (
  <div className="flex items-start justify-between mb-6">
    <div className="flex items-start gap-3">
      {Icon && (
        <div className="w-10 h-10 rounded-lg bg-teal-400/10 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Icon className="w-5 h-5 text-teal-400" />
        </div>
      )}
      <div>
        <h1 className="text-xl font-bold text-white">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
    {actions && <div className="flex items-center gap-2">{actions}</div>}
  </div>
);

// ===== LOADING SKELETON =====
export const Skeleton = ({ className = '' }) => (
  <div className={`animate-pulse bg-[#161618] rounded-lg ${className}`}></div>
);

export const LoadingState = () => (
  <div className="flex items-center justify-center py-16">
    <div className="flex items-center gap-3 text-gray-500">
      <div className="w-5 h-5 border-2 border-teal-400/20 border-t-teal-400 rounded-full animate-spin"></div>
      <span className="text-sm">Loading...</span>
    </div>
  </div>
);

// ===== EMPTY STATE =====
export const EmptyState = ({ icon: Icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-16 text-center">
    {Icon && <Icon className="w-12 h-12 text-gray-700 mb-4" />}
    <h3 className="text-sm font-medium text-gray-400">{title}</h3>
    {description && <p className="text-xs text-gray-600 mt-1 max-w-sm">{description}</p>}
    {action && <div className="mt-4">{action}</div>}
  </div>
);

// ===== MODAL =====
export const Modal = ({ open, onClose, title, children, size = 'md' }) => {
  if (!open) return null;
  const sizes = { sm: 'max-w-md', md: 'max-w-lg', lg: 'max-w-2xl', xl: 'max-w-4xl' };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className={`w-full ${sizes[size]} bg-[#111113] border border-[#1f1f23] rounded-xl shadow-xl`} onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-[#1f1f23]">
          <h2 className="text-base font-semibold text-white">{title}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <div className="p-4 max-h-[70vh] overflow-y-auto">{children}</div>
      </div>
    </div>
  );
};

// ===== TOGGLE =====
export const Toggle = ({ checked, onChange, label }) => (
  <label className="flex items-center gap-2 cursor-pointer">
    <div className={`relative w-9 h-5 rounded-full transition-colors ${checked ? 'bg-teal-400' : 'bg-[#2a2a2e]'}`} onClick={() => onChange(!checked)}>
      <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${checked ? 'translate-x-4' : 'translate-x-0.5'}`}></div>
    </div>
    {label && <span className="text-sm text-gray-400">{label}</span>}
  </label>
);

// ===== PROGRESS BAR =====
export const ProgressBar = ({ value, max = 100, color = 'bg-teal-400', height = 'h-1.5' }) => (
  <div className={`w-full ${height} bg-[#1f1f23] rounded-full overflow-hidden`}>
    <div className={`${height} ${color} rounded-full transition-all`} style={{ width: `${Math.min((value / max) * 100, 100)}%` }}></div>
  </div>
);

// ===== SECTION DIVIDER =====
export const SectionDivider = ({ label }) => (
  <div className="flex items-center gap-3 my-4">
    <div className="h-px flex-1 bg-[#1f1f23]"></div>
    {label && <span className="text-xs text-gray-600 font-medium uppercase tracking-wider">{label}</span>}
    <div className="h-px flex-1 bg-[#1f1f23]"></div>
  </div>
);
