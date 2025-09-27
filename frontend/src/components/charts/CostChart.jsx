import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import Card from '../common/Card';

const CostChart = ({ data, title = "Cost Trends vs Budget" }) => {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis 
            dataKey="name" 
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
          <Area
            type="monotone"
            dataKey="budget"
            stackId="1"
            stroke="#e2e8f0"
            fill="#f8fafc"
            fillOpacity={0.6}
            name="Budget"
          />
          <Area
            type="monotone"
            dataKey="cost"
            stackId="2"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.6}
            name="Actual Cost"
          />
          <Legend />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default CostChart;