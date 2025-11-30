import React, { useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle, X } from 'lucide-react';

const Toast = ({ message, type = 'success', onClose, duration = 3000 }) => {
  useEffect(() => {
    if (duration) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const icons = {
    success: <CheckCircle className="h-5 w-5 text-green-400" />,
    error: <XCircle className="h-5 w-5 text-red-400" />,
    warning: <AlertCircle className="h-5 w-5 text-yellow-400" />,
    info: <AlertCircle className="h-5 w-5 text-blue-400" />
  };

  const colors = {
    success: 'bg-green-900/20 border-green-500/50',
    error: 'bg-red-900/20 border-red-500/50',
    warning: 'bg-yellow-900/20 border-yellow-500/50',
    info: 'bg-blue-900/20 border-blue-500/50'
  };

  return (
    <div
      className={`fixed top-24 right-6 z-50 flex items-center space-x-3 px-4 py-3 rounded-xl border backdrop-blur-sm shadow-cosmic-lg animate-slide-in-right ${colors[type]}`}
      style={{ minWidth: '300px', maxWidth: '500px' }}
    >
      {icons[type]}
      <p className="flex-1 text-sm text-cosmic-txt-1 font-medium">{message}</p>
      <button
        onClick={onClose}
        className="text-cosmic-muted hover:text-cosmic-txt-1 transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

export default Toast;
