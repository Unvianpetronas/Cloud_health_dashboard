import React, { useState, useEffect } from 'react';
import { RefreshCw, DollarSign, TrendingUp, TrendingDown, PieChart as PieChartIcon, BarChart3, AlertCircle, AlertTriangle, ExternalLink } from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/common/Header';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import costExplorerApi from '../services/costExplorerApi';
import logger from '../utils/logger';

const CostExplorer = () => {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [costExplorerEnabled, setCostExplorerEnabled] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState(30); // days

  useEffect(() => {
    if (isAuthenticated) {
      fetchCostData();
    }
  }, [isAuthenticated, timeRange]);

  const fetchCostData = async () => {
    setLoading(true);
    setError(null);

    const result = await costExplorerApi.getSummary(timeRange, 'DAILY', 30, false);

    if (result.success) {
      // Check if Cost Explorer is enabled
      if (result.data.enabled === false) {
        setCostExplorerEnabled(false);
        setData(null);
        logger.warn('Cost Explorer is not enabled for this account');
      } else {
        setCostExplorerEnabled(true);
        setData(result.data);
        logger.info('Cost data loaded successfully');
      }
    } else {
      setError(result.error);
      logger.error('Failed to load cost data:', result.error);
    }

    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    const result = await costExplorerApi.getSummary(timeRange, 'DAILY', 30, true);

    if (result.success) {
      if (result.data.enabled === false) {
        setCostExplorerEnabled(false);
        setData(null);
      } else {
        setCostExplorerEnabled(true);
        setData(result.data);
        logger.info('Cost data refreshed');
      }
    } else {
      setError(result.error);
    }

    setRefreshing(false);
  };

  const formatCurrency = (amount) => {
    if (!amount || isNaN(amount)) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const getTotalCost = () => {
    return data?.total_cost?.total_cost || 0;
  };

  const getCostByServiceData = () => {
    if (!data?.by_service?.by_service) return [];

    return Object.entries(data.by_service.by_service)
        .map(([service, cost]) => ({
          name: service.replace('Amazon ', '').replace('AWS ', ''),
          value: parseFloat(cost) || 0
        }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 8);
  };

  const getCostTrendData = () => {
    if (!data?.total_cost?.by_time) return [];

    return data.total_cost.by_time.map(item => ({
      date: new Date(item.time_period.start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      cost: parseFloat(item.total.unblended_cost.amount) || 0
    }));
  };

  const getForecastData = () => {
    if (!data?.forecast?.forecast_data) return [];

    return data.forecast.forecast_data.map(item => ({
      date: new Date(item.time_period.start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      forecast: parseFloat(item.mean_value) || 0
    }));
  };

  const getForecastTotal = () => {
    return data?.forecast?.total_forecast || 0;
  };

  const getCostTrend = () => {
    const costData = getCostTrendData();
    if (costData.length < 2) return 0;

    const recent = costData.slice(-7).reduce((sum, item) => sum + item.cost, 0) / 7;
    const previous = costData.slice(-14, -7).reduce((sum, item) => sum + item.cost, 0) / 7;

    if (previous === 0) return 0;
    return ((recent - previous) / previous) * 100;
  };

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#84cc16'];

  // --- UI STATES ---

  // 1. Cost Explorer Not Enabled UI
  if (!loading && !costExplorerEnabled) {
    return (
        <div className="min-h-screen bg-cosmic-bg-0">
          <Header title="Cost Explorer" showNavigation={true} />
          <main className="container mx-auto px-6 py-8">
            <Card className="p-8 animate-fade-in max-w-4xl mx-auto">
              <div className="text-center">
                <div className="flex justify-center mb-4">
                  <div className="bg-yellow-500/10 p-4 rounded-full">
                    <AlertTriangle className="h-16 w-16 text-yellow-400" />
                  </div>
                </div>

                <h2 className="text-2xl font-bold text-cosmic-txt-1 mb-3">
                  Cost Explorer Not Enabled
                </h2>

                <p className="text-cosmic-txt-2 mb-6 max-w-2xl mx-auto">
                  AWS Cost Explorer is currently not enabled for your account, or data is still being ingested.
                  You'll need to enable Cost Explorer in the AWS Console to view cost analytics.
                </p>

                {/* Instructions */}
                <div className="bg-cosmic-bg-2 border border-cosmic-border rounded-xl p-6 mb-6 text-left max-w-2xl mx-auto">
                  <h3 className="text-lg font-semibold text-cosmic-txt-1 mb-4 flex items-center">
                    <span className="bg-blue-500/10 text-blue-400 rounded-full w-8 h-8 flex items-center justify-center mr-3 font-bold">1</span>
                    Enable Cost Explorer
                  </h3>
                  <div className="ml-11 space-y-3">
                    <p className="text-cosmic-txt-2 text-sm">
                      • Go to <a href="https://console.aws.amazon.com/billing/home#/" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 inline-flex items-center">AWS Billing Dashboard <ExternalLink size={14} className="ml-1" /></a>
                    </p>
                    <p className="text-cosmic-txt-2 text-sm">• Navigate to "Cost Explorer" in the left sidebar</p>
                    <p className="text-cosmic-txt-2 text-sm">• Click "Enable Cost Explorer"</p>
                  </div>
                </div>

                <div className="flex justify-center space-x-4">
                  <Button onClick={handleRefresh} disabled={refreshing} variant="primary" className="flex items-center space-x-2">
                    {refreshing ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                          <span>Checking...</span>
                        </>
                    ) : (
                        <>
                          <RefreshCw size={18} />
                          <span>Check Again</span>
                        </>
                    )}
                  </Button>
                </div>
              </div>
            </Card>
          </main>
        </div>
    );
  }

  // 2. Loading State
  if (loading) {
    return (
        <div className="min-h-screen bg-cosmic-bg-0">
          <Header title="Cost Explorer" showNavigation={true} />
          <main className="container mx-auto px-6 py-8 flex items-center justify-center min-h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
              <p className="text-cosmic-txt-2">Loading cost data...</p>
            </div>
          </main>
        </div>
    );
  }

  // 3. Error State
  if (error) {
    return (
        <div className="min-h-screen bg-cosmic-bg-0">
          <Header title="Cost Explorer" showNavigation={true} />
          <main className="container mx-auto px-6 py-8 flex items-center justify-center min-h-96">
            <Card className="p-8 text-center max-w-md animate-scale-in">
              <AlertCircle className="h-16 w-16 text-red-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-cosmic-txt-1 mb-2">Failed to Load Cost Data</h2>
              <p className="text-cosmic-txt-2 mb-4">{error}</p>
              <Button onClick={fetchCostData} variant="primary">Retry</Button>
            </Card>
          </main>
        </div>
    );
  }

  const costTrend = getCostTrend();
  const costByService = getCostByServiceData();
  const costTrendData = getCostTrendData();
  const forecastData = getForecastData();

  return (
      <div className="min-h-screen bg-cosmic-bg-0">
        <Header title="Cost Explorer" showNavigation={true} />

        {/* Updated Main Container to match Dashboard style */}
        <main className="container mx-auto px-6 py-8 space-y-6">

          {/* Title & Controls */}
          <div className="flex flex-col md:flex-row justify-between items-center animate-fade-in">
            <div className="mb-4 md:mb-0">
              <h1 className="text-3xl font-bold text-cosmic-txt-1 mb-2">AWS Cost Explorer</h1>
              <p className="text-cosmic-txt-2">Analyze and optimize your AWS spending</p>
            </div>

            <div className="flex items-center space-x-3 bg-cosmic-card p-2 rounded-xl border border-cosmic-border backdrop-blur-sm">
              <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(parseInt(e.target.value))}
                  className="px-4 py-2 bg-cosmic-bg-2 border border-cosmic-border rounded-lg text-cosmic-txt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              >
                  <option value={7}>Last 7 days</option>
                <option value={14}>Last 14 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
              </select>
              <Button
                  onClick={handleRefresh}
                  disabled={refreshing}
                  variant="primary"
                  className="flex items-center space-x-2 text-sm py-2"
              >
                {refreshing ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></div>
                      <span>Refreshing</span>
                    </>
                ) : (
                    <>
                      <RefreshCw size={16} />
                      <span>Refresh</span>
                    </>
                )}
              </Button>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6 animate-slide-up">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="text-sm text-cosmic-txt-2 mb-1">Total Cost ({timeRange} days)</div>
                  <div className="text-3xl font-bold text-cosmic-txt-1">
                    {formatCurrency(getTotalCost())}
                  </div>
                </div>
                <div className="p-3 bg-green-500/10 rounded-lg">
                  <DollarSign className="h-8 w-8 text-green-400" />
                </div>
              </div>
            </Card>

            <Card className="p-6 animate-slide-up" style={{animationDelay: '0.1s'}}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="text-sm text-cosmic-txt-2 mb-1">30-Day Forecast</div>
                  <div className="text-3xl font-bold text-cosmic-txt-1">
                    {formatCurrency(getForecastTotal())}
                  </div>
                </div>
                <div className="p-3 bg-blue-500/10 rounded-lg">
                  <TrendingUp className="h-8 w-8 text-blue-400" />
                </div>
              </div>
            </Card>

            <Card className="p-6 animate-slide-up" style={{animationDelay: '0.2s'}}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="text-sm text-cosmic-txt-2 mb-1">Weekly Trend</div>
                  <div className={`text-3xl font-bold ${costTrend >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {costTrend >= 0 ? '+' : ''}{costTrend.toFixed(1)}%
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${costTrend >= 0 ? 'bg-red-500/10' : 'bg-green-500/10'}`}>
                  {costTrend >= 0 ? (
                      <TrendingUp className="h-8 w-8 text-red-400" />
                  ) : (
                      <TrendingDown className="h-8 w-8 text-green-400" />
                  )}
                </div>
              </div>
            </Card>
          </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Cost Trend */}
            {costTrendData.length > 0 && (
                <Card className="p-6 animate-slide-up" style={{animationDelay: '0.3s'}}>
                  <div className="flex items-center mb-6">
                    <div className="p-2 bg-blue-500/10 rounded-lg mr-3">
                      <BarChart3 className="h-5 w-5 text-blue-400" />
                    </div>
                    <h2 className="text-lg font-semibold text-cosmic-txt-1">Daily Cost Trend</h2>
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={costTrendData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                      <XAxis
                          dataKey="date"
                          tick={{ fill: '#9ca3af', fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                          dy={10}
                      />
                      <YAxis
                          tick={{ fill: '#9ca3af', fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                          tickFormatter={(value) => `$${value}`}
                      />
                      <Tooltip
                          contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', color: '#f3f4f6' }}
                          itemStyle={{ color: '#fff' }}
                          formatter={(value) => formatCurrency(value)}
                      />
                      <Line type="monotone" dataKey="cost" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, fill: '#1d4ed8' }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
            )}

            {/* Cost by Service */}
            {costByService.length > 0 && (
                <Card className="p-6 animate-slide-up" style={{animationDelay: '0.4s'}}>
                  <div className="flex items-center mb-6">
                    <div className="p-2 bg-purple-500/10 rounded-lg mr-3">
                      <PieChartIcon className="h-5 w-5 text-purple-400" />
                    </div>
                    <h2 className="text-lg font-semibold text-cosmic-txt-1">Cost by Service</h2>
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                          data={costByService}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => percent > 0.05 ? `${name} ${(percent * 100).toFixed(0)}%` : ''}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                      >
                        {costByService.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                          contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', color: '#f3f4f6' }}
                          itemStyle={{ color: '#fff' }}
                          formatter={(value) => formatCurrency(value)}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </Card>
            )}
          </div>

          {/* Forecast Chart */}
          {forecastData.length > 0 && (
              <Card className="p-6 animate-slide-up" style={{animationDelay: '0.5s'}}>
                <div className="flex items-center mb-6">
                  <div className="p-2 bg-cyan-500/10 rounded-lg mr-3">
                    <TrendingUp className="h-5 w-5 text-cyan-400" />
                  </div>
                  <h2 className="text-lg font-semibold text-cosmic-txt-1">30-Day Cost Forecast</h2>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={forecastData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                    <XAxis
                        dataKey="date"
                        tick={{ fill: '#9ca3af', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        dy={10}
                    />
                    <YAxis
                        tick={{ fill: '#9ca3af', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(value) => `$${value}`}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', color: '#f3f4f6' }}
                        itemStyle={{ color: '#fff' }}
                        formatter={(value) => [formatCurrency(value), "Forecast"]}
                    />
                    <Line
                        type="monotone"
                        dataKey="forecast"
                        stroke="#06b6d4"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={{ r: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
          )}

          {/* Service Breakdown Table */}
          {costByService.length > 0 && (
              <Card className="p-6 animate-slide-up" style={{animationDelay: '0.6s'}}>
                <h2 className="text-lg font-semibold text-cosmic-txt-1 mb-4">Service Cost Breakdown</h2>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                    <tr className="border-b border-cosmic-border">
                      <th className="text-left py-3 px-4 text-xs font-semibold text-cosmic-muted uppercase tracking-wider">Service</th>
                      <th className="text-right py-3 px-4 text-xs font-semibold text-cosmic-muted uppercase tracking-wider">Cost</th>
                      <th className="text-right py-3 px-4 text-xs font-semibold text-cosmic-muted uppercase tracking-wider">Percentage</th>
                    </tr>
                    </thead>
                    <tbody>
                    {costByService.map((service, index) => {
                      const totalCost = costByService.reduce((sum, s) => sum + s.value, 0);
                      const percentage = (service.value / totalCost) * 100;

                      return (
                          <tr key={index} className="border-b border-cosmic-border/50 hover:bg-cosmic-bg-2 transition-colors">
                            <td className="py-3 px-4 text-sm text-cosmic-txt-1 font-medium flex items-center space-x-3">
                              <div
                                  className="w-2.5 h-2.5 rounded-full shadow-sm"
                                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                              ></div>
                              <span>{service.name}</span>
                            </td>
                            <td className="py-3 px-4 text-sm text-cosmic-txt-1 text-right font-bold">
                              {formatCurrency(service.value)}
                            </td>
                            <td className="py-3 px-4 text-sm text-cosmic-txt-2 text-right">
                              {percentage.toFixed(1)}%
                            </td>
                          </tr>
                      );
                    })}
                    </tbody>
                  </table>
                </div>
              </Card>
          )}
        </main>
      </div>
  );
};

export default CostExplorer;