import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            🎉 React App is Working!
          </h1>
          <p className="text-gray-600 mb-6">
            Your setup is successful. The app compiled without errors.
          </p>
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            <strong>Success!</strong> All components are loading correctly.
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;