// Enhanced cosmic starfield animation utility
export const createStarfield = (containerId = 'starfield') => {
  const container = document.getElementById(containerId) || document.body;
  
  // Create starfield container
  const starfield = document.createElement('div');
  starfield.id = 'cosmic-starfield';
  starfield.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: -1;
    overflow: hidden;
  `;
  
  // Generate different types of stars
  const starCount = 150;
  const shootingStarCount = 3;
  
  // Regular stars
  for (let i = 0; i < starCount; i++) {
    const star = document.createElement('div');
    const size = Math.random() * 3 + 0.5;
    const opacity = Math.random() * 0.9 + 0.1;
    const x = Math.random() * 100;
    const y = Math.random() * 100;
    const duration = Math.random() * 4 + 2;
    const delay = Math.random() * 2;
    const brightness = Math.random() > 0.7 ? 'bright' : 'normal';
    
    star.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      background: ${brightness === 'bright' ? 'rgba(255, 255, 255, 1)' : `rgba(255, 255, 255, ${opacity})`};
      border-radius: 50%;
      left: ${x}%;
      top: ${y}%;
      animation: twinkle ${duration}s ease-in-out infinite alternate;
      animation-delay: ${delay}s;
      box-shadow: ${brightness === 'bright' ? '0 0 6px rgba(255, 255, 255, 0.8), 0 0 12px rgba(59, 130, 246, 0.3)' : 'none'};
    `;
    
    starfield.appendChild(star);
  }
  
  // Shooting stars
  for (let i = 0; i < shootingStarCount; i++) {
    const shootingStar = document.createElement('div');
    const startX = Math.random() * 100;
    const startY = Math.random() * 50;
    const length = Math.random() * 100 + 50;
    const angle = Math.random() * 45 + 15;
    const duration = Math.random() * 2 + 1;
    const delay = Math.random() * 10;
    
    shootingStar.style.cssText = `
      position: absolute;
      width: ${length}px;
      height: 2px;
      background: linear-gradient(90deg, rgba(255, 255, 255, 0.8) 0%, rgba(59, 130, 246, 0.6) 50%, transparent 100%);
      left: ${startX}%;
      top: ${startY}%;
      transform: rotate(${angle}deg);
      animation: shootingStar ${duration}s linear infinite;
      animation-delay: ${delay}s;
      opacity: 0;
    `;
    
    starfield.appendChild(shootingStar);
  }
  
  // Add enhanced CSS animations
  if (!document.getElementById('starfield-styles')) {
    const style = document.createElement('style');
    style.id = 'starfield-styles';
    style.textContent = `
      @keyframes twinkle {
        0% { 
          opacity: 0.2; 
          transform: scale(1) rotate(0deg); 
        }
        50% { 
          opacity: 1; 
          transform: scale(1.1) rotate(180deg); 
        }
        100% { 
          opacity: 0.3; 
          transform: scale(0.9) rotate(360deg); 
        }
      }
      
      @keyframes shootingStar {
        0% { 
          opacity: 0; 
          transform: translateX(-100px) rotate(${Math.random() * 45 + 15}deg); 
        }
        10% { 
          opacity: 1; 
        }
        90% { 
          opacity: 1; 
        }
        100% { 
          opacity: 0; 
          transform: translateX(100vw) rotate(${Math.random() * 45 + 15}deg); 
        }
      }
      
      @keyframes cosmicPulse {
        0%, 100% { 
          box-shadow: 0 0 6px rgba(255, 255, 255, 0.8), 0 0 12px rgba(59, 130, 246, 0.3);
        }
        50% { 
          box-shadow: 0 0 12px rgba(255, 255, 255, 1), 0 0 24px rgba(59, 130, 246, 0.6);
        }
      }
    `;
    document.head.appendChild(style);
  }
  
  container.appendChild(starfield);
  
  return starfield;
};

export const removeStarfield = () => {
  const starfield = document.getElementById('cosmic-starfield');
  if (starfield) {
    starfield.remove();
  }
};