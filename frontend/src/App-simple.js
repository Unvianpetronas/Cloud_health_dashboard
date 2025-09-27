import React from 'react';

function App() {
  return (
    <div className="App">
      <header className="bg-blue-600 text-white p-4">
        <h1 className="text-2xl font-bold">AWS Cloud Health Dashboard</h1>
      </header>
      <main className="p-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Welcome!</h2>
          <p className="text-gray-600">
            Your dashboard is loading. If you see this message, the basic setup is working.
          </p>
          <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Test Button
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;