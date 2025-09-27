import React from 'react';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  disabled = false, 
  loading = false,
  onClick,
  className = '',
  ...props 
}) => {
  const baseStyles = 'btn inline-flex items-center justify-center font-semibold focus-ring';
  
  const variants = {
    primary: 'btn-primary',
    secondary: 'bg-cosmic-card text-cosmic-txt-1 border-cosmic-border hover:bg-cosmic-bg-2',
    success: 'bg-cosmic-success text-white hover:bg-green-600 shadow-cosmic-glow',
    danger: 'bg-red-600 text-white hover:bg-red-700 shadow-cosmic-glow',
    outline: 'btn-ghost',
    ghost: 'btn-ghost'
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };
  
  const disabledStyles = disabled || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:animate-float';
  
  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${disabledStyles} ${className}`}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {children}
    </button>
  );
};

export default Button;