import React, { useState, useCallback } from 'react';
import { 
  DollarSign, 
  Server, 
  AlertTriangle, 
  Zap,
  Activity,
  Database,
  Shield,
  TrendingUp
} from 'lucide-react';

// Import components
import Header from '../components/common/Header';
import MetricsCard from '../components/dashboard/MetricsCard';
import CostChart from '../components/charts/CostChart';
import ServiceHealthChart from '../components/charts/ServiceHealthChart';
import PerformanceChart from '../components/charts/PerformanceChart';
import AlertsPanel from '../components/dashboard/AlertsPanel';
import ServiceStatusList from '../components/dashboard/ServiceStatusList';
import Loading from '../components/common/Loading';

// Import hooks
import useDashboardData from '../hooks/useDashboardData';
import { useAuth } from '../contexts/AuthContext';

const Home = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const { user, logout } = useAuth();
  const { data, loading, error, lastUpdated, refresh } = useDashboardData(selectedTimeRange);

  // Prepare metrics data with icons
  const metricsData = data.metrics ? data.metrics.map((metric, index) => {
    const icons = [DollarSign, Server, AlertTriangle, Zap];
    const iconColors = ["#3b82f6", "#10b981", "#ef4444", "#0ea5e9"];
    const iconBgColors = ["#dbeafe", "#d1fae5", "#fef2f2", "#f0f9ff"];
    
    return {
      ...metric,
      icon: icons[index],
      iconColor: iconColors[index],
      iconBgColor: iconBgColors[index]
    };
  }) : [];

  const handleRefresh = useCallback(() => {
    refresh();
  }, [refresh]);

  const handleTimeRangeChange = useCallback((timeRange) => {
    setSelectedTimeRange(timeRange);
  }, []);

  // Show loading state
  if (loading && !data.metrics) {
    return (
      <div className="min-h-screen">
        <Header
          onRefresh={handleRefresh}
          refreshing={loading}
          selectedTimeRange={selectedTimeRange}
          onTimeRangeChange={handleTimeRangeChange}
        />
        <main className="container mx-auto px-6 flex items-center justify-center min-h-96">
          <div className="card p-8 text-center">
            <Loading size="lg" text="Loading dashboard data..." />
          </div>
        </main>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen">
        <Header
          onRefresh={handleRefresh}
          refreshing={loading}
          selectedTimeRange={selectedTimeRange}
          onTimeRangeChange={handleTimeRangeChange}
        />
        <main className="container mx-auto px-6 flex items-center justify-center min-h-96">
          <div className="card p-8 text-center">
            <AlertTriangle size={48} className="mx-auto text-red-500 mb-4 animate-pulse" />
            <h3 className="text-lg font-medium text-cosmic-txt-1 mb-2">Failed to load dashboard</h3>
            <p className="text-cosmic-txt-2 mb-4">{error}</p>
            <button
              onClick={handleRefresh}
              className="btn btn-primary"
            >
              Try Again
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Header
        onRefresh={handleRefresh}
        refreshing={loading}
        selectedTimeRange={selectedTimeRange}
        onTimeRangeChange={handleTimeRangeChange}
      />

      {/* Cosmic Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="badge mb-6 animate-fade-in">
            <span className="text-cosmic-txt-2">New Features Available</span>
          </div>
          <h1 className="hero-title">
            AWS Cloud Health
            <br />
            Dashboard
          </h1>
          <p className="hero-subtitle">
            Monitor your cloud infrastructure with real-time insights, performance metrics, 
            and intelligent alerts in a beautiful cosmic interface.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mt-8">
            <button className="btn btn-primary px-8 py-3 animate-float">
              View Dashboard
            </button>
            <button className="btn btn-ghost px-8 py-3">
              Learn More
            </button>
          </div>
          
          {/* Trusted by section */}
          <div className="mt-16 pt-8 border-t border-cosmic-border/30">
            <p className="text-cosmic-muted text-sm mb-6">Trusted by leading organizations</p>
            <div className="flex flex-wrap justify-center items-center gap-8 opacity-60">
              <div className="text-cosmic-txt-2 font-semibold">AWS</div>
              <div className="text-cosmic-txt-2 font-semibold">Microsoft</div>
              <div className="text-cosmic-txt-2 font-semibold">Google Cloud</div>
              <div className="text-cosmic-txt-2 font-semibold">IBM</div>
              <div className="text-cosmic-txt-2 font-semibold">Oracle</div>
            </div>
          </div>
        </div>
      </section>

      <main className="container mx-auto px-6">
        {/* Metrics Cards */}
        <section className="py-16">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {metricsData.map((metric, index) => (
              <div key={index} className="card p-6 animate-fade-in" style={{animationDelay: `${index * 0.1}s`}}>
                <MetricsCard
                  title={metric.title}
                  value={metric.value}
                  change={metric.change}
                  changeType={metric.changeType}
                  icon={metric.icon}
                  iconColor={metric.iconColor}
                  iconBgColor={metric.iconBgColor}
                />
              </div>
            ))}
          </div>
        </section>

        {/* Charts Section */}
        <section className="py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2 card p-6">
              <CostChart data={data.costs || []} />
            </div>
            <div className="card p-6">
              <ServiceHealthChart data={data.serviceHealth || []} />
            </div>
          </div>
        </section>

        {/* Performance Chart */}
        <section className="py-8">
          <div className="card p-6 mb-8">
            <PerformanceChart data={data.performance || []} />
          </div>
        </section>

        {/* Bottom Section */}
        <section className="py-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-6">
              <AlertsPanel alerts={data.alerts || []} />
            </div>
            <div className="card p-6">
              <ServiceStatusList services={data.serviceStatus || []} />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Home;