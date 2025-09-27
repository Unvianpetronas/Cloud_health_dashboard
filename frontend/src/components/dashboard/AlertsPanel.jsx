import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import Card from '../common/Card';

const AlertsPanel = ({ alerts = [], title = "Recent Alerts" }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#ef4444';
      case 'warning': return '#f59e0b';
      case 'info': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  const getSeverityBgColor = (severity) => {
    switch (severity) {
      case 'critical': return '#fef2f2';
      case 'warning': return '#fffbeb';
      case 'info': return '#eff6ff';
      default: return '#f9fafb';
    }
  };

  return (
    <Card padding="p-0">
      <div className="p-6 border-b border-gray-200 flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-gray-500 hover:text-gray-700 transition-colors"
        >
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
      </div>

      {isExpanded && (
        <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <AlertTriangle size={48} className="mx-auto mb-2 opacity-50" />
              <p>No alerts at this time</p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                className="p-4 rounded-lg border transition-all duration-200 hover:shadow-sm"
                style={{
                  borderColor: getSeverityColor(alert.severity),
                  backgroundColor: getSeverityBgColor(alert.severity)
                }}
              >
                <div className="flex items-start space-x-3">
                  <AlertTriangle 
                    size={16} 
                    color={getSeverityColor(alert.severity)}
                    className="mt-0.5 flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      <span
                        className="text-xs font-semibold uppercase px-2 py-1 rounded"
                        style={{
                          color: getSeverityColor(alert.severity),
                          backgroundColor: 'white'
                        }}
                      >
                        {alert.severity}
                      </span>
                      <span className="text-sm text-gray-600">
                        {alert.service} • {alert.region}
                      </span>
                    </div>
                    <p className="text-sm text-gray-800 mb-2 leading-relaxed">
                      {alert.message}
                    </p>
                    <p className="text-xs text-gray-500">
                      {alert.timestamp}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </Card>
  );
};

export default AlertsPanel;