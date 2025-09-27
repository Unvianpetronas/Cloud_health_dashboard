import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import Card from '../common/Card';

const PerformanceChart = ({ data, title = "Performance Metrics (Last 24 Hours)" }) => {
  const metrics = [
    { key: 'cpu', name: 'CPU %', color: '#ef4444' },
    { key: 'memory', name: 'Memory %', color: '#3b82f6' },
    { key: 'network', name: 'Network %', color: '#10b981' },
    { key: 'storage', name: 'Storage %', color: '#f59e0b' }
  ];

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis 
            dataKey="time" 
            stroke="#64748b" 
            fontSize={12}
            tick={{ fill: '#64748b' }}
          />
          <YAxis 
            stroke="#64748b" 
            fontSize={12}
            tick={{ fill: '#64748b' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: '0.375rem',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
          />
          <Legend />
          {metrics.map(metric => (
            <Line
              key={metric.key}
              type="monotone"
              dataKey={metric.key}
              stroke={metric.color}
              strokeWidth={2}
              name={metric.name}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default PerformanceChart;