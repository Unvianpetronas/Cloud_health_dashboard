import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, BarChart3, Settings, Shield, Database, DollarSign } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
    { path: '/architecture', label: 'Architecture', icon: Shield },
    { path: '/s3', label: 'S3 Buckets', icon: Database },
    { path: '/costs', label: 'Cost Explorer', icon: DollarSign },
    { path: '/settings', label: 'Settings', icon: Settings }
  ];

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="mx-6 mb-6">
      <div className="navbar">
        <div className="flex space-x-2">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`nav-link inline-flex items-center px-4 py-2 text-sm font-medium transition-all duration-300 ${
                isActive(path) ? 'active' : ''
              }`}
            >
              <Icon size={16} className="mr-2 opacity-70" />
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;