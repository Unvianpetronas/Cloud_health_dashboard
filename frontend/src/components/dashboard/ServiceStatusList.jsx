import React from 'react';
import { CheckCircle, AlertTriangle, Monitor } from 'lucide-react';
import Card from '../common/Card';

const ServiceStatusList = ({ services = [], title = "Service Status" }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle size={16} />;
      case 'warning': return <AlertTriangle size={16} />;
      case 'critical': return <AlertTriangle size={16} />;
      default: return <Monitor size={16} />;
    }
  };

  const getStatusBadge = (status) => {
    const color = getStatusColor(status);
    return (
      <span
        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize"
        style={{
          color: color,
          backgroundColor: `${color}20`
        }}
      >
        {status}
      </span>
    );
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div className="space-y-3">
        {services.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Monitor size={48} className="mx-auto mb-2 opacity-50" />
            <p>No services to display</p>
          </div>
        ) : (
          services.map((service, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div style={{ color: getStatusColor(service.status) }}>
                  {getStatusIcon(service.status)}
                </div>
                <div>
                  <p className="font-medium text-gray-900">{service.name}</p>
                  <p className="text-sm text-gray-600">{service.region}</p>
                </div>
              </div>

              <div className="text-right">
                <p className="font-medium text-gray-900 mb-1">
                  {service.instances} instances
                </p>
                {getStatusBadge(service.status)}
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
};

export default ServiceStatusList;