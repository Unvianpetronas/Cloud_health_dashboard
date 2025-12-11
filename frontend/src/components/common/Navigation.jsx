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
    { path: '/costs', label: 'Cost Explorer', icon: DollarSign }
  ];

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="mx-3 sm:mx-6 mb-4 sm:mb-6">
      <div className="navbar">
      <div className="flex space-x-1 sm:space-x-2 overflow-x-auto scrollbar-hide pb-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`nav-link inline-flex items-center px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium transition-all duration-300 whitespace-nowrap flex-shrink-0 ${
                isActive(path) ? 'active' : ''
              }`}
            >
              <Icon size={14} className="sm:w-4 sm:h-4 w-3.5 h-3.5 mr-1 sm:mr-2 opacity-70" />
              <span className="hidden xs:inline">{label}</span>
              <span className="xs:hidden">{label.split(' ')[0]}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;