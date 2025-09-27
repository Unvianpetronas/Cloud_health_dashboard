// Test file to check for syntax errors
import React from 'react';

// Test imports
import Button from './components/common/Button';
import Card from './components/common/Card';
import Loading from './components/common/Loading';
import Header from './components/common/Header';
import MetricsCard from './components/dashboard/MetricsCard';

console.log('All components imported successfully');

// Test basic component creation
const TestComponent = () => {
  return (
    <div>
      <Card>
        <h1>Test</h1>
        <Button variant="primary">Test Button</Button>
        <Loading />
      </Card>
    </div>
  );
};

export default TestComponent;