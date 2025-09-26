// File: frontend/src/App.js

import React from 'react';
// SOLUTION for #3: Import Routes and Route from react-router-dom
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Import your page components
import Dashboard from './pages/Dashboard';
// Import other pages as you create them
// import Settings from './pages/Settings';

function App() {
  return (
      <Router>
        {/* You can wrap this in a Layout component later */}
        <div>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            {/* Add routes for other pages here */}
            {/* <Route path="/settings" element={<Settings />} /> */}
          </Routes>
        </div>
      </Router>
  );
}

// SOLUTION for #2: Add the default export line
export default App;