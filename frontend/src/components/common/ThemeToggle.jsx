import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const ThemeToggle = ({ className = '' }) => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative inline-flex items-center justify-center w-12 h-6 
        bg-gray-200 dark:bg-gray-700 rounded-full transition-colors duration-300
        focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
        dark:focus:ring-offset-gray-800 ${className}
      `}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <div
        className={`
          absolute w-5 h-5 bg-white dark:bg-gray-200 rounded-full shadow-md
          transform transition-transform duration-300 flex items-center justify-center
          ${isDark ? 'translate-x-3' : '-translate-x-3'}
        `}
      >
        {isDark ? (
          <Moon size={12} className="text-gray-700" />
        ) : (
          <Sun size={12} className="text-yellow-500" />
        )}
      </div>
      
      {/* Background icons */}
      <div className="absolute inset-0 flex items-center justify-between px-1">
        <Sun 
          size={14} 
          className={`text-yellow-500 transition-opacity duration-300 ${
            isDark ? 'opacity-30' : 'opacity-70'
          }`} 
        />
        <Moon 
          size={14} 
          className={`text-gray-400 transition-opacity duration-300 ${
            isDark ? 'opacity-70' : 'opacity-30'
          }`} 
        />
      </div>
    </button>
  );
};

export default ThemeToggle;