import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, Home, ArrowLeft } from 'lucide-react';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Cosmic Hero Background */}
      <div className="hero absolute inset-0 -z-10"></div>

      <div className="max-w-2xl w-full mx-auto px-6 animate-fade-in">
        <div className="card p-12 text-center">
          {/* Error Icon */}
          <div className="mb-8 flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-yellow-500/20 blur-3xl animate-pulse"></div>
              <div className="relative bg-gradient-to-br from-yellow-500/20 to-orange-500/20 p-6 rounded-3xl backdrop-blur-sm border border-yellow-500/30">
                <AlertTriangle size={80} className="text-yellow-400 animate-float" />
              </div>
            </div>
          </div>

          {/* Error Message */}
          <h1 className="text-8xl font-bold bg-gradient-to-r from-yellow-400 via-orange-400 to-red-400 bg-clip-text text-transparent mb-4 animate-glow">
            404
          </h1>

          <h2 className="text-3xl font-bold text-cosmic-txt-1 mb-4">
            Page Not Found
          </h2>

          <p className="text-cosmic-txt-2 text-lg mb-8 max-w-md mx-auto">
            The page you're looking for doesn't exist or has been moved.
            Let's get you back on track.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button
              onClick={() => navigate(-1)}
              className="btn btn-ghost flex items-center space-x-2 w-full sm:w-auto"
            >
              <ArrowLeft size={20} />
              <span>Go Back</span>
            </button>

            <button
              onClick={() => navigate('/')}
              className="btn btn-primary flex items-center space-x-2 w-full sm:w-auto"
            >
              <Home size={20} />
              <span>Go to Dashboard</span>
            </button>
          </div>

          {/* Additional Info */}
          <div className="mt-12 pt-8 border-t border-cosmic-border">
            <p className="text-sm text-cosmic-muted">
              If you believe this is an error, please contact support.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
