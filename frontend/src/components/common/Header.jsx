import React, { useState, useEffect } from 'react';
import { Cloud, RefreshCw } from 'lucide-react';
import Navigation from './Navigation';
import UserMenu from './UserMenu';

const Header = ({
                    title = "AWS Cloud Health Dashboard",
                    onRefresh,
                    refreshing = false,
                    showNavigation = true,

                }) => {
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div>
            <header className="navbar navbar--header mx-3 sm:mx-6 mt-2 sm:mt-4 mb-2">
                <div className="flex justify-between items-center gap-2 sm:gap-4">

                    {/* --- LEFT: Logo & Title --- */}
                    <div className="flex items-center space-x-2 sm:space-x-4 min-w-0 flex-shrink-0">
                        <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-1.5 sm:p-2 rounded-xl shadow-cosmic-glow flex-shrink-0">
                            <Cloud size={20} className="sm:w-7 sm:h-7 w-5 h-5 text-white" />
                        </div>
                        <div className="min-w-0">
                            <h1 className="text-base sm:text-xl font-bold text-cosmic-txt-1 truncate">
                                {title}
                            </h1>
                            <div className="badge mt-1 animate-fade-in text-xs hidden sm:block">
                                Real-time Monitoring
                            </div>
                        </div>
                    </div>

                    {/* --- RIGHT: Controls & User Menu --- */}
                    <div className="flex items-center space-x-2 sm:space-x-3 md:space-x-4 flex-shrink-0">
                        {/* Last Updated Time */}
                        {onRefresh && (
                            <div className="text-xs sm:text-sm text-cosmic-txt-2 hidden lg:block border-r border-gray-700 pr-3 sm:pr-4 mr-1">
                                {currentTime.toLocaleTimeString()}
                            </div>
                        )}

                        {/* Refresh Button */}
                        {onRefresh && (
                            <button
                                onClick={onRefresh}
                                disabled={refreshing}
                                className="btn btn-primary flex items-center space-x-1 sm:space-x-2 text-xs sm:text-sm px-2 sm:px-3 py-1 sm:py-1.5"
                            >
                                <RefreshCw size={14} className={`sm:w-4 sm:h-4 w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                                <span className="hidden sm:inline">Refresh</span>
                            </button>
                        )}

                        {/* User Menu */}
                        <UserMenu />
                    </div>

                </div>
            </header>

            {showNavigation && <Navigation />}
        </div>
    );
};

export default Header;