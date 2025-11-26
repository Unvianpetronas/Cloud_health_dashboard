import React, { useState, useEffect } from 'react';
import { Cloud, RefreshCw } from 'lucide-react';
import Navigation from './Navigation';
import UserMenu from './UserMenu';

const Header = ({
                  title = "AWS Cloud Health Dashboard",
                  onRefresh,
                  refreshing = false,
                  selectedTimeRange = '24h',
                  onTimeRangeChange,
                  showNavigation = true
                }) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const timeRangeOptions = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ];

  return (
      <div>
        <header className="navbar navbar--header mx-6 mt-4 mb-2">
          <div className="flex justify-between items-center">
            {/* Left: Logo and Title */}
            <div className="flex items-center space-x-4">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-2 rounded-xl shadow-cosmic-glow">
                <Cloud size={28} className="text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-cosmic-txt-1">
                  {title}
                </h1>
                <div className="badge mt-1 animate-fade-in">
                  ✨ Real-time Monitoring
                </div>
              </div>
            </div>

            {/* Right: Controls and User Menu */}
            <div className="flex items-center space-x-4">
              {/* Time Range Selector */}
              {onTimeRangeChange && (
                  <select
                      value={selectedTimeRange}
                      onChange={(e) => onTimeRangeChange?.(e.target.value)}
                      className="px-3 py-2 border border-cosmic-border rounded-xl bg-cosmic-card text-cosmic-txt-1 text-sm focus-ring backdrop-blur-cosmic"
                  >
                    {timeRangeOptions.map(option => (
                        <option key={option.value} value={option.value} className="bg-cosmic-bg-1">
                          {option.label}
                        </option>
                    ))}
                  </select>
              )}

              {/* Refresh Button */}
              {onRefresh && (
                  <button
                      onClick={onRefresh}
                      disabled={refreshing}
                      className="btn btn-primary flex items-center space-x-2 text-sm"
                  >
                    <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
                    <span className="hidden sm:inline">Refresh</span>
                  </button>
              )}

              {/* Last Updated Time */}
              {onRefresh && (
                  <div className="text-sm text-cosmic-txt-2 hidden md:block">
                    {currentTime.toLocaleTimeString()}
                  </div>
              )}

              {/* User Menu - NEW! */}
              <UserMenu />
            </div>
          </div>
        </header>

        {showNavigation && <Navigation />}
      </div>
  );
};

export default Header;