import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, LogOut, Home, Settings, ChevronDown } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const UserMenu = () => {
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef(null);
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleNavigate = (path) => {
        navigate(path);
        setIsOpen(false);
    };

    return (
        <div className="relative" ref={menuRef}>
            {/* User Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center space-x-3 px-4 py-2 rounded-xl border border-cosmic-border bg-cosmic-card hover:bg-cosmic-bg-2 transition-all duration-200 backdrop-blur-cosmic group"
            >
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center shadow-cosmic-glow">
                    <User size={16} className="text-white" />
                </div>
                <div className="text-left hidden sm:block">
                    <p className="text-sm font-medium text-cosmic-txt-1">
                        {user?.accessKey || 'User'}
                    </p>
                    <p className="text-xs text-cosmic-txt-2">AWS Account</p>
                </div>
                <ChevronDown
                    size={16}
                    className={`text-cosmic-muted transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                />
            </button>

            {/* Dropdown Menu */}
            {isOpen && (
                <div
                    className="user-menu-dropdown absolute right-0 top-full mt-4 w-64 card p-2 shadow-cosmic-glow-lg animate-scale-in z-50"
                    style={{ animationDuration: '0.2s' }}
                >
                    {/* User Info */}
                    <div className="px-4 py-3 border-b border-cosmic-border mb-2">
                        <p className="text-sm font-semibold text-cosmic-txt-1 mb-1">
                            Signed in as
                        </p>
                        <p className="text-xs text-cosmic-txt-2 truncate">
                            {user?.accessKey || 'Unknown User'}
                        </p>
                        {user?.loginTime && (
                            <p className="text-xs text-cosmic-muted mt-1">
                                Since {new Date(user.loginTime).toLocaleTimeString()}
                            </p>
                        )}
                    </div>

                    {/* Menu Items */}
                    <div className="space-y-1">
                        <button
                            onClick={() => handleNavigate('/')}
                            className="w-full flex items-center space-x-3 px-4 py-2 rounded-lg text-cosmic-txt-2 hover:text-cosmic-txt-1 hover:bg-cosmic-bg-2 transition-all duration-200 group"
                        >
                            <Home size={16} className="group-hover:text-blue-400" />
                            <span className="text-sm font-medium">Home</span>
                        </button>

                        <button
                            onClick={() => handleNavigate('/dashboard')}
                            className="w-full flex items-center space-x-3 px-4 py-2 rounded-lg text-cosmic-txt-2 hover:text-cosmic-txt-1 hover:bg-cosmic-bg-2 transition-all duration-200 group"
                        >
                            <Home size={16} className="group-hover:text-blue-400" />
                            <span className="text-sm font-medium">Dashboard</span>
                        </button>

                        <button
                            onClick={() => handleNavigate('/settings')}
                            className="w-full flex items-center space-x-3 px-4 py-2 rounded-lg text-cosmic-txt-2 hover:text-cosmic-txt-1 hover:bg-cosmic-bg-2 transition-all duration-200 group"
                        >
                            <Settings size={16} className="group-hover:text-blue-400" />
                            <span className="text-sm font-medium">Settings</span>
                        </button>
                    </div>

                    {/* Divider */}
                    <div className="border-t border-cosmic-border my-2"></div>

                    {/* Logout */}
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center space-x-3 px-4 py-2 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-900/20 transition-all duration-200 group"
                    >
                        <LogOut size={16} />
                        <span className="text-sm font-medium">Sign Out</span>
                    </button>
                </div>
            )}
        </div>
    );
};

export default UserMenu;