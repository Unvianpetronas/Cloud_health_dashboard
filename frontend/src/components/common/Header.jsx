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
            <header className="navbar navbar--header mx-6 mt-4 mb-2">
              
                <div className="flex justify-between items-center gap-4">

                    <div className="flex items-center space-x-4">
                        <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-2 rounded-xl shadow-cosmic-glow">
                            <Cloud size={28} className="text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-cosmic-txt-1">
                                {title}
                            </h1>
                            <div className="badge mt-1 animate-fade-in">
                                Real-time Monitoring
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center space-x-3 md:space-x-4">

                        {/* Last Updated Time */}
                        {onRefresh && (
                            <div className="text-sm text-cosmic-txt-2 hidden md:block border-r border-gray-700 pr-4 mr-1">
                                {currentTime.toLocaleTimeString()}
                            </div>
                        )}

                        {/* Refresh Button */}
                        {onRefresh && (
                            <button
                                onClick={onRefresh}
                                disabled={refreshing}
                                className="btn btn-primary flex items-center space-x-2 text-sm px-3 py-1.5"
                            >
                                <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
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