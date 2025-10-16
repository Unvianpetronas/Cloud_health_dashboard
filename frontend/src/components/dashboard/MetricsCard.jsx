import React from 'react';
import Card from '../common/Card';

const MetricsCard = ({
                       title,
                       value,
                       change,
                       changeType = 'positive',
                       icon: Icon,
                       iconColor = '#3b82f6',
                       iconBgColor = '#dbeafe'
                     }) => {
  const getChangeColor = () => {
    switch (changeType) {
      case 'positive': return 'text-cosmic-success';
      case 'negative': return 'text-red-400';
      default: return 'text-cosmic-muted';
    }
  };

  const getChangeIcon = () => {
    if (changeType === 'positive') return '↑';
    if (changeType === 'negative') return '↓';
    return '';
  };

  return (
      <div className="overflow-visible">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <p className="text-sm font-medium text-cosmic-txt-2 mb-2">{title}</p>
            <p className="text-3xl font-bold text-cosmic-txt-1 mb-3">{value}</p>
            {change && (
                <p className={`text-sm font-medium ${getChangeColor()}`}>
                  {getChangeIcon()} {change}
                </p>
            )}
          </div>

          {Icon && (
              <div className="relative group flex-shrink-0">
                <div
                    className="p-4 rounded-xl backdrop-blur-cosmic transition-all duration-300 group-hover:scale-110 relative"
                    style={{
                      backgroundColor: 'rgba(59, 130, 246, 0.15)',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      boxShadow: '0 8px 25px rgba(59, 130, 246, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
                      minWidth: '60px',
                      minHeight: '60px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                >
                  <Icon size={28} className="text-blue-400 opacity-80 group-hover:opacity-100 transition-opacity" />

                  {/* ✅ Decorative pulse dot - now properly positioned */}
                  <div
                      className="absolute w-3 h-3 bg-gradient-to-r from-blue-400 to-blue-500 rounded-full animate-pulse group-hover:animate-glow"
                      style={{
                        top: '-4px',
                        right: '-4px'
                      }}
                  ></div>
                </div>

                {/* ✅ Background glow effect */}
                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
              </div>
          )}
        </div>
      </div>
  );
};

export default MetricsCard;