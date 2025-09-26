/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Cosmic color palette
        cosmic: {
          'bg-0': '#0b1020',
          'bg-1': '#0e1430', 
          'bg-2': '#111836',
          'txt-1': '#e6e9f5',
          'txt-2': '#b7c0d9',
          'muted': '#8b93ad',
          'pri': '#3b82f6',
          'pri-2': '#60a5fa',
          'card': 'rgba(15, 20, 40, 0.8)',
          'border': '#1f2a44',
          'ring': '#6ea8ff',
          'success': '#22c55e',
          'warning': '#f59e0b',
        },
        // Keep AWS colors for compatibility
        aws: {
          orange: '#FF9900',
          'orange-dark': '#FF7700',
          'orange-light': '#FFB84D',
          dark: '#232F3E',
          'dark-light': '#37475A',
          blue: '#4A90E2',
          'blue-light': '#6BA3F0',
          gray: '#F2F3F3',
        },
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        }
      },
      boxShadow: {
        'cosmic': '0 10px 30px rgba(0, 0, 0, 0.35)',
        'cosmic-lg': '0 20px 40px rgba(0, 0, 0, 0.4)',
        'cosmic-glow': '0 0 20px rgba(59, 130, 246, 0.55)',
        'cosmic-glow-lg': '0 0 30px rgba(59, 130, 246, 0.55), 0 0 40px rgba(59, 130, 246, 0.55)',
      },
      borderRadius: {
        'cosmic': '1.25rem',
      },
      backdropBlur: {
        'cosmic': '12px',
      }
    },
  },
  plugins: [],
}