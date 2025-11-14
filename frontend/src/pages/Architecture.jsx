import React, { useState, useEffect } from 'react';
import { RefreshCw, TrendingUp, Shield, DollarSign, Zap, Activity, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, PieChart, Pie, Cell, Legend, Tooltip } from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/common/Header';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import architectureApi from '../services/architectureApi';
import logger from '../utils/logger';

const Architecture = () => {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedPriority, setSelectedPriority] = useState('ALL');

  useEffect(() => {
    if (isAuthenticated) {
      fetchArchitectureData();
    }
  }, [isAuthenticated]);

  const fetchArchitectureData = async () => {
    setLoading(true);
    setError(null);

    const result = await architectureApi.analyze(false, true);

    if (result.success) {
      setData(result.data);
      logger.info('Architecture data loaded successfully');
    } else {
      setError(result.error);
      logger.error('Failed to load architecture data:', result.error);
    }

    setLoading(false);
  };

  const handleRefresh = async () => {
    setAnalyzing(true);
    const result = await architectureApi.analyze(true, true);

    if (result.success) {
      setData(result.data);
      logger.info('Architecture analysis refreshed');
    } else {
      setError(result.error);
    }

    setAnalyzing(false);
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreGradient = (score) => {
    if (score >= 80) return 'from-green-500 to-emerald-600';
    if (score >= 60) return 'from-yellow-500 to-orange-600';
    return 'from-red-500 to-rose-600';
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'CRITICAL': return <XCircle className="h-5 w-5 text-red-400" />;
      case 'HIGH': return <AlertTriangle className="h-5 w-5 text-orange-400" />;
      case 'MEDIUM': return <Activity className="h-5 w-5 text-yellow-400" />;
      case 'LOW': return <CheckCircle className="h-5 w-5 text-blue-400" />;
      default: return <Activity className="h-5 w-5 text-gray-400" />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'CRITICAL': return 'border-red-500 bg-red-500/10';
      case 'HIGH': return 'border-orange-500 bg-orange-500/10';
      case 'MEDIUM': return 'border-yellow-500 bg-yellow-500/10';
      case 'LOW': return 'border-blue-500 bg-blue-500/10';
      default: return 'border-gray-500 bg-gray-500/10';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cosmic-bg-0">
        <Header title="Architecture Analysis" showNavigation={true} />
        <main className="p-6 max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-cosmic-bg-0">
        <Header title="Architecture Analysis" showNavigation={true} />
        <main className="p-6 max-w-7xl mx-auto">
          <Card className="p-8 text-center">
            <AlertTriangle className="h-16 w-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-cosmic-txt-1 mb-2">Analysis Error</h2>
            <p className="text-cosmic-txt-2 mb-4">{error}</p>
            <Button onClick={fetchArchitectureData} variant="primary">
              Retry
            </Button>
          </Card>
        </main>
      </div>
    );
  }

  const wellArchitectedData = data?.well_architected_framework?.pillars
    ? Object.entries(data.well_architected_framework.pillars).map(([name, pillar]) => ({
        pillar: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        score: pillar.score,
        fullMark: 100
      }))
    : [];

  const filteredRecommendations = selectedPriority === 'ALL'
    ? data?.recommendations || []
    : (data?.recommendations || []).filter(rec => rec.priority === selectedPriority);

  const priorityCounts = {
    CRITICAL: (data?.recommendations || []).filter(r => r.priority === 'CRITICAL').length,
    HIGH: (data?.recommendations || []).filter(r => r.priority === 'HIGH').length,
    MEDIUM: (data?.recommendations || []).filter(r => r.priority === 'MEDIUM').length,
    LOW: (data?.recommendations || []).filter(r => r.priority === 'LOW').length
  };

  return (
    <div className="min-h-screen bg-cosmic-bg-0">
      <Header title="Architecture Analysis" showNavigation={true} />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header Actions */}
        <div className="flex justify-between items-center animate-fade-in">
          <div>
            <h1 className="text-3xl font-bold text-cosmic-txt-1 mb-2">Architecture Health</h1>
            <p className="text-cosmic-txt-2">
              Last analyzed: {data?.analysis_timestamp ? new Date(data.analysis_timestamp).toLocaleString() : 'Never'}
            </p>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={analyzing}
            variant="primary"
            className="flex items-center space-x-2"
          >
            {analyzing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <RefreshCw size={18} />
                <span>Refresh Analysis</span>
              </>
            )}
          </Button>
        </div>

        {/* Overall Score */}
        <Card className="p-8 text-center animate-fade-in" style={{animationDelay: '0.1s'}}>
          <div className="mb-4">
            <div className={`text-7xl font-bold bg-gradient-to-r ${getScoreGradient(data?.overall_score || 0)} bg-clip-text text-transparent`}>
              {data?.overall_score || 0}
            </div>
            <div className="text-2xl font-semibold text-cosmic-txt-1 mt-2">
              {data?.overall_rating || 'Unknown'}
            </div>
          </div>
          <p className="text-cosmic-txt-2 max-w-2xl mx-auto">
            Your AWS architecture has been analyzed against industry best practices and the AWS Well-Architected Framework.
          </p>
        </Card>

        {/* AWS Well-Architected Framework Pillars */}
        <Card className="p-6 animate-fade-in" style={{animationDelay: '0.2s'}}>
          <div className="flex items-center mb-6">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center mr-3 shadow-cosmic-glow">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-cosmic-txt-1">AWS Well-Architected Framework</h2>
          </div>

          {wellArchitectedData.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="flex items-center justify-center">
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={wellArchitectedData}>
                    <PolarGrid stroke="#374151" />
                    <PolarAngleAxis dataKey="pillar" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#9ca3af' }} />
                    <Radar name="Score" dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="space-y-3">
                {wellArchitectedData.map((pillar, index) => (
                  <div key={index} className="bg-cosmic-bg-2 p-4 rounded-xl border border-cosmic-border">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold text-cosmic-txt-1">{pillar.pillar}</span>
                      <span className={`text-lg font-bold ${getScoreColor(pillar.score)}`}>{pillar.score}</span>
                    </div>
                    <div className="w-full bg-cosmic-bg-1 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full bg-gradient-to-r ${getScoreGradient(pillar.score)}`}
                        style={{ width: `${pillar.score}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-center text-cosmic-txt-2 py-8">No pillar data available</p>
          )}
        </Card>

        {/* Recommendations */}
        <Card className="p-6 animate-fade-in" style={{animationDelay: '0.3s'}}>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mr-3 shadow-cosmic-glow">
                <TrendingUp className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-xl font-semibold text-cosmic-txt-1">Recommendations ({filteredRecommendations.length})</h2>
            </div>

            <div className="flex space-x-2">
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(priority => (
                <button
                  key={priority}
                  onClick={() => setSelectedPriority(priority)}
                  className={`px-3 py-1 rounded-lg text-sm font-semibold transition-all ${
                    selectedPriority === priority
                      ? 'bg-blue-500 text-white'
                      : 'bg-cosmic-bg-2 text-cosmic-txt-2 hover:bg-cosmic-bg-1'
                  }`}
                >
                  {priority}
                  {priority !== 'ALL' && (
                    <span className="ml-1 text-xs">({priorityCounts[priority]})</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {filteredRecommendations.length > 0 ? (
              filteredRecommendations.map((rec, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-xl border-2 ${getPriorityColor(rec.priority)} transition-all hover:scale-[1.02]`}
                >
                  <div className="flex items-start space-x-3">
                    {getPriorityIcon(rec.priority)}
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-semibold text-cosmic-txt-1">{rec.title}</h3>
                        <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
                          rec.priority === 'CRITICAL' ? 'bg-red-500 text-white' :
                          rec.priority === 'HIGH' ? 'bg-orange-500 text-white' :
                          rec.priority === 'MEDIUM' ? 'bg-yellow-500 text-black' :
                          'bg-blue-500 text-white'
                        }`}>
                          {rec.priority}
                        </span>
                      </div>
                      <p className="text-sm text-cosmic-txt-2 mb-2">{rec.description}</p>
                      {rec.impact && (
                        <div className="flex items-center space-x-2 text-xs text-cosmic-txt-2">
                          <Zap size={12} className="text-yellow-400" />
                          <span>Impact: {rec.impact}</span>
                        </div>
                      )}
                      {rec.estimated_savings && (
                        <div className="flex items-center space-x-2 text-xs text-green-400 mt-1">
                          <DollarSign size={12} />
                          <span>Potential savings: ${rec.estimated_savings}/month</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-center text-cosmic-txt-2 py-8">No recommendations for this priority level</p>
            )}
          </div>
        </Card>
      </main>
    </div>
  );
};

export default Architecture;
