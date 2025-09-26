import React from 'react';

const Card = ({ 
  children, 
  className = '', 
  padding = 'p-6',
  shadow = 'shadow-cosmic',
  hover = true,
  ...props 
}) => {
  const baseStyles = 'card';
  const hoverStyles = hover ? 'hover:shadow-cosmic-lg hover:-translate-y-1 transition-all duration-300' : '';
  
  return (
    <div 
      className={`${baseStyles} ${shadow} ${padding} ${hoverStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;