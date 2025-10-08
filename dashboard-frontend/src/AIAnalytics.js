import React, { useState, useEffect, useCallback } from 'react';
import config from './config';
import './App.css';

function AIAnalytics({ sourceKey }) {
  const [patterns, setPatterns] = useState([]);
  const [trends, setTrends] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('patterns');
  const [filters, setFilters] = useState({
    patternType: '',
    severity: '',
    trendType: '',
    timeframe: '1h'
  });

  // Fetch AI analytics data
  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [patternsRes, trendsRes, summaryRes] = await Promise.all([
        fetch(`${config.API_BASE_URL}/api/ai/patterns?` + new URLSearchParams({
          pattern_type: filters.patternType || undefined,
          severity: filters.severity || undefined,
          limit: 20
        }).toString(), { credentials: 'include' }),
        fetch(`${config.API_BASE_URL}/api/ai/trends?` + new URLSearchParams({
          trend_type: filters.trendType || undefined,
          timeframe: filters.timeframe
        }).toString(), { credentials: 'include' }),
        fetch(`${config.API_BASE_URL}/api/ai/analytics/summary`, { credentials: 'include' })
      ]);

      const [patternsData, trendsData, summaryData] = await Promise.all([
        patternsRes.json(),
        trendsRes.json(),
        summaryRes.json()
      ]);

      setPatterns(patternsData.patterns || []);
      setTrends(trendsData.trends || []);
      setSummary(summaryData);
      
    } catch (err) {
      setError('Failed to load AI analytics');
      console.error('Analytics fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchAnalytics, sourceKey]);

  // Export functionality
  const handleExport = async (format) => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/ai/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          format: format,
          include_patterns: true,
          include_trends: true,
          include_raw_data: format === 'json'
        })
      });
      
      const data = await response.json();
      
      if (format === 'json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ai-analytics-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === 'csv' && data.files) {
        Object.entries(data.files).forEach(([filename, content]) => {
          const blob = new Blob([content], { type: 'text/csv' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          a.click();
          URL.revokeObjectURL(url);
        });
      }
      
    } catch (err) {
      setError('Export failed');
      console.error('Export error:', err);
    }
  };

  // Loading state
  if (loading && patterns.length === 0 && trends.length === 0) {
    return (
      <div className="log-card">
        <div className="card-header">
          <h3 className="card-title">🤖 AI Analytics</h3>
          <div className="status-indicator status-warning">Loading...</div>
        </div>
        <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.8)' }}>
          <div style={{
            width: 50,
            height: 50,
            border: '4px solid rgba(255,255,255,0.3)',
            borderTop: '4px solid white',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          Analyzing patterns and trends with AI...
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="log-card">
        <div className="card-header">
          <h3 className="card-title">🤖 AI Analytics</h3>
          <div className="status-indicator status-error">Error</div>
        </div>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
          <p style={{ color: 'rgba(255,255,255,0.8)', marginBottom: 24 }}>{error}</p>
          <button
            onClick={fetchAnalytics}
            className="btn-modern glow-primary"
            style={{
              background: 'var(--primary-gradient)',
              padding: '14px 28px',
              borderRadius: 16,
              color: 'white',
              border: 'none',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
          >
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="log-card">
      {/* Header with Summary */}
      <div className="card-header">
        <h3 className="card-title">🤖 AI Analytics Dashboard</h3>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div className="status-indicator status-success">
            {summary.summary?.total_patterns_detected || 0} patterns
          </div>
          <div className="status-indicator status-warning">
            {summary.summary?.total_trends_identified || 0} trends
          </div>
          <div className="status-indicator status-error">
            Risk: {summary.risk_assessment?.risk_level || 'UNKNOWN'}
          </div>
        </div>
      </div>

      {/* Action Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 24,
        padding: 16,
        background: 'rgba(255,255,255,0.1)',
        borderRadius: 12
      }}>
        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: 8 }}>
          {[
            { id: 'patterns', label: '🔍 Patterns', count: patterns.length },
            { id: 'trends', label: '📈 Trends', count: trends.length },
            { id: 'summary', label: '📊 Summary', count: null }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 20px',
                background: activeTab === tab.id 
                  ? 'var(--primary-gradient)'
                  : 'var(--glass-bg)',
                color: 'white',
                border: activeTab === tab.id ? 'none' : '1px solid var(--border-color)',
                borderRadius: 12,
                fontSize: 14,
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: activeTab === tab.id ? 'var(--shadow-colored)' : 'none'
              }}
            >
              {tab.label} {tab.count !== null && `(${tab.count})`}
            </button>
          ))}
        </div>

        {/* Export Controls */}
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => handleExport('json')}
            style={{
              padding: '10px 20px',
              background: 'var(--secondary-gradient)',
              color: 'white',
              border: 'none',
              borderRadius: 12,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: '0 6px 20px rgba(6, 182, 212, 0.3)'
            }}
          >
            📄 Export JSON
          </button>
          <button
            onClick={() => handleExport('csv')}
            style={{
              padding: '10px 20px',
              background: 'var(--success-gradient)',
              color: 'white',
              border: 'none',
              borderRadius: 12,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: '0 6px 20px rgba(16, 185, 129, 0.3)'
            }}
          >
            📊 Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      {(activeTab === 'patterns' || activeTab === 'trends') && (
        <div style={{
          display: 'flex',
          gap: 12,
          marginBottom: 24,
          padding: 16,
          background: 'rgba(255,255,255,0.05)',
          borderRadius: 12,
          flexWrap: 'wrap'
        }}>
          {activeTab === 'patterns' && (
            <>
              <select
                value={filters.severity}
                onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value }))}
                style={{
                  padding: '8px 12px',
                  background: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14
                }}
              >
                <option value="">All Severities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
              <input
                type="text"
                placeholder="Pattern type..."
                value={filters.patternType}
                onChange={(e) => setFilters(prev => ({ ...prev, patternType: e.target.value }))}
                style={{
                  padding: '8px 12px',
                  background: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14,
                  minWidth: 150
                }}
              />
            </>
          )}
          
          {activeTab === 'trends' && (
            <>
              <select
                value={filters.timeframe}
                onChange={(e) => setFilters(prev => ({ ...prev, timeframe: e.target.value }))}
                style={{
                  padding: '8px 12px',
                  background: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14
                }}
              >
                <option value="15m">Last 15 minutes</option>
                <option value="1h">Last hour</option>
                <option value="6h">Last 6 hours</option>
                <option value="24h">Last 24 hours</option>
              </select>
              <input
                type="text"
                placeholder="Trend type..."
                value={filters.trendType}
                onChange={(e) => setFilters(prev => ({ ...prev, trendType: e.target.value }))}
                style={{
                  padding: '8px 12px',
                  background: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14,
                  minWidth: 150
                }}
              />
            </>
          )}
        </div>
      )}

      {/* Content based on active tab */}
      {activeTab === 'patterns' && (
        <div>
          <h4 style={{ color: 'white', marginBottom: 16, fontSize: 18 }}>
            🔍 Detected Patterns ({patterns.length})
          </h4>
          {patterns.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.8)' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
              <p>No patterns detected with current filters</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: 16 }}>
              {patterns.map((pattern, idx) => (
                <div key={idx} style={{
                  background: 'rgba(255,255,255,0.1)',
                  padding: 20,
                  borderRadius: 12,
                  border: `1px solid ${
                    pattern.severity === 'critical' ? 'rgba(248, 113, 113, 0.6)' :
                    pattern.severity === 'high' ? 'rgba(251, 191, 36, 0.6)' :
                    pattern.severity === 'medium' ? 'rgba(96, 165, 250, 0.6)' : 'rgba(52, 211, 153, 0.6)'
                  }`,
                  borderLeft: `4px solid ${
                    pattern.severity === 'critical' ? '#f87171' :
                    pattern.severity === 'high' ? '#fbbf24' :
                    pattern.severity === 'medium' ? '#60a5fa' : '#34d399'
                  }`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                    <div>
                      <h5 style={{ color: 'white', margin: '0 0 8px 0', fontSize: 16, fontWeight: 700 }}>
                        {pattern.type || 'Unknown Pattern'}
                      </h5>
                      <p style={{ color: 'rgba(255,255,255,0.8)', margin: 0, fontSize: 14 }}>
                        {pattern.description || 'No description available'}
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <span style={{
                        background: pattern.severity === 'critical' ? 'linear-gradient(135deg, #f87171 0%, #ef4444 50%, #dc2626 100%)' :
                                  pattern.severity === 'high' ? 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%)' :
                                  pattern.severity === 'medium' ? 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%)' : 
                                  'linear-gradient(135deg, #34d399 0%, #10b981 50%, #059669 100%)',
                        color: 'white',
                        padding: '6px 12px',
                        borderRadius: 8,
                        fontSize: 12,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
                      }}>
                        {pattern.severity}
                      </span>
                      <span style={{
                        background: 'rgba(255,255,255,0.2)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600
                      }}>
                        {pattern.confidence}% confidence
                      </span>
                    </div>
                  </div>
                  
                  {pattern.actionable_insights && pattern.actionable_insights.length > 0 && (
                    <div style={{ marginTop: 16 }}>
                      <h6 style={{ color: 'white', margin: '0 0 8px 0', fontSize: 14, fontWeight: 600 }}>
                        💡 Recommended Actions:
                      </h6>
                      <ul style={{ margin: 0, paddingLeft: 20, color: 'rgba(255,255,255,0.8)', fontSize: 13 }}>
                        {pattern.actionable_insights.map((insight, i) => (
                          <li key={i}>{insight}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'trends' && (
        <div>
          <h4 style={{ color: 'white', marginBottom: 16, fontSize: 18 }}>
            📈 Identified Trends ({trends.length})
          </h4>
          {trends.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.8)' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>📈</div>
              <p>No trends identified with current filters</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: 16 }}>
              {trends.map((trend, idx) => (
                <div key={idx} style={{
                  background: 'rgba(255,255,255,0.1)',
                  padding: 20,
                  borderRadius: 12,
                  border: '1px solid rgba(255,255,255,0.2)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                    <div>
                      <h5 style={{ color: 'white', margin: '0 0 8px 0', fontSize: 16, fontWeight: 700 }}>
                        {trend.type || 'Unknown Trend'}
                      </h5>
                      <p style={{ color: 'rgba(255,255,255,0.8)', margin: 0, fontSize: 14 }}>
                        {trend.description || 'Trend detected in log patterns'}
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexDirection: 'column', alignItems: 'flex-end' }}>
                      <span style={{
                        background: 'rgba(52, 152, 219, 0.8)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600
                      }}>
                        {trend.count || 0}x occurrences
                      </span>
                      {trend.trend_direction && (
                        <span style={{
                          background: trend.trend_direction === 'increasing' ? '#e74c3c' :
                                    trend.trend_direction === 'decreasing' ? '#2ecc71' : '#f39c12',
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: 6,
                          fontSize: 12,
                          fontWeight: 600
                        }}>
                          {trend.trend_direction === 'increasing' ? '📈 Rising' :
                           trend.trend_direction === 'decreasing' ? '📉 Falling' : '➡️ Stable'}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {trend.forecast && (
                    <div style={{
                      background: 'rgba(255,255,255,0.05)',
                      padding: 12,
                      borderRadius: 8,
                      marginTop: 12
                    }}>
                      <h6 style={{ color: 'white', margin: '0 0 8px 0', fontSize: 14, fontWeight: 600 }}>
                        🔮 Forecast ({trend.timeframe}):
                      </h6>
                      <p style={{ color: 'rgba(255,255,255,0.8)', margin: 0, fontSize: 13 }}>
                        Predicted {trend.forecast.predicted_count} occurrences
                        (Confidence: {trend.forecast.confidence})
                      </p>
                    </div>
                  )}
                  
                  {trend.recommended_actions && trend.recommended_actions.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <h6 style={{ color: 'white', margin: '0 0 8px 0', fontSize: 14, fontWeight: 600 }}>
                        💡 Recommendations:
                      </h6>
                      <ul style={{ margin: 0, paddingLeft: 20, color: 'rgba(255,255,255,0.8)', fontSize: 13 }}>
                        {trend.recommended_actions.map((action, i) => (
                          <li key={i}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'summary' && (
        <div>
          <h4 style={{ color: 'white', marginBottom: 24, fontSize: 18 }}>
            📊 Analytics Summary
          </h4>
          
          {/* Risk Assessment */}
          {summary.risk_assessment && (
            <div style={{
              background: 'rgba(255,255,255,0.1)',
              padding: 20,
              borderRadius: 12,
              marginBottom: 24,
              border: `2px solid ${
                summary.risk_assessment.risk_level === 'HIGH' ? '#e74c3c' :
                summary.risk_assessment.risk_level === 'MEDIUM' ? '#f39c12' : '#2ecc71'
              }`
            }}>
              <h5 style={{ color: 'white', margin: '0 0 12px 0', fontSize: 16, fontWeight: 700 }}>
                🎯 Risk Assessment
              </h5>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
                <div style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: summary.risk_assessment.risk_level === 'HIGH' ? '#e74c3c' :
                        summary.risk_assessment.risk_level === 'MEDIUM' ? '#f39c12' : '#2ecc71'
                }}>
                  {summary.risk_assessment.risk_level}
                </div>
                <div>
                  <div style={{ color: 'white', fontSize: 14, fontWeight: 600 }}>
                    Risk Score: {summary.risk_assessment.risk_score}/100
                  </div>
                  <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12 }}>
                    Based on {summary.risk_assessment.factors?.total_patterns || 0} patterns, 
                    {' '}{summary.risk_assessment.factors?.total_trends || 0} trends
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* System Recommendations */}
          {summary.recommendations && summary.recommendations.length > 0 && (
            <div style={{
              background: 'rgba(255,255,255,0.1)',
              padding: 20,
              borderRadius: 12,
              marginBottom: 24
            }}>
              <h5 style={{ color: 'white', margin: '0 0 12px 0', fontSize: 16, fontWeight: 700 }}>
                🎯 System Recommendations
              </h5>
              <ul style={{ margin: 0, paddingLeft: 20, color: 'rgba(255,255,255,0.8)' }}>
                {summary.recommendations.map((rec, idx) => (
                  <li key={idx} style={{ marginBottom: 8 }}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Statistics Grid */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: 16,
            marginBottom: 24
          }}>
            <div style={{
              background: 'rgba(255,255,255,0.1)',
              padding: 16,
              borderRadius: 12,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#3498db', marginBottom: 8 }}>
                {summary.summary?.total_patterns_detected || 0}
              </div>
              <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 14 }}>
                Patterns Detected
              </div>
            </div>
            
            <div style={{
              background: 'rgba(255,255,255,0.1)',
              padding: 16,
              borderRadius: 12,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#e67e22', marginBottom: 8 }}>
                {summary.summary?.total_trends_identified || 0}
              </div>
              <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 14 }}>
                Trends Identified
              </div>
            </div>
            
            <div style={{
              background: 'rgba(255,255,255,0.1)',
              padding: 16,
              borderRadius: 12,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#2ecc71', marginBottom: 8 }}>
                {summary.summary?.logs_analyzed || 0}
              </div>
              <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 14 }}>
                Logs Analyzed
              </div>
            </div>
            
            <div style={{
              background: 'rgba(255,255,255,0.1)',
              padding: 16,
              borderRadius: 12,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#9b59b6', marginBottom: 8 }}>
                {summary.summary?.bedrock_status === 'enabled' ? '✓' : '✗'}
              </div>
              <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 14 }}>
                AI Status
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AIAnalytics;
