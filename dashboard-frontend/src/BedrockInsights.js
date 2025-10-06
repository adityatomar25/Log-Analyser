import React, { useState, useEffect } from 'react';
import { FaBrain, FaRobot, FaChartLine, FaExclamationTriangle } from 'react-icons/fa';

function BedrockInsights() {
  const [bedrockStatus, setBedrockStatus] = useState({});
  const [insights, setInsights] = useState({});
  const [predictions, setPredictions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchBedrockData();
    const interval = setInterval(fetchBedrockData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchBedrockData = async () => {
    try {
      setLoading(true);
      
      // Fetch Bedrock status
      const statusRes = await fetch('http://localhost:8000/api/bedrock/status', {
        credentials: 'include'
      });
      const statusData = await statusRes.json();
      setBedrockStatus(statusData);

      // Fetch insights if Bedrock is available
      if (statusData.enabled && statusData.available) {
        const [insightsRes, predictionsRes] = await Promise.all([
          fetch('http://localhost:8000/api/bedrock/insights', { credentials: 'include' }),
          fetch('http://localhost:8000/api/bedrock/predictions', { credentials: 'include' })
        ]);

        const insightsData = await insightsRes.json();
        const predictionsData = await predictionsRes.json();

        setInsights(insightsData);
        setPredictions(predictionsData);
      }

      setError('');
    } catch (err) {
      setError('Failed to fetch Bedrock data');
      console.error('Bedrock data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleBedrock = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/bedrock/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ enabled: !bedrockStatus.enabled })
      });

      const data = await response.json();
      setBedrockStatus(prev => ({ ...prev, ...data }));
      
      // Refresh data after toggle
      setTimeout(fetchBedrockData, 1000);
    } catch (err) {
      setError('Failed to toggle Bedrock');
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    const colors = {
      low: '#27ae60',
      medium: '#f39c12', 
      high: '#e74c3c',
      critical: '#8e44ad'
    };
    return colors[riskLevel] || '#7f8c8d';
  };

  if (loading && !bedrockStatus.enabled) {
    return (
      <div style={{
        background: '#fff',
        borderRadius: 12,
        padding: 24,
        boxShadow: '0 2px 8px #0001',
        marginBottom: 24
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
          <FaBrain style={{ marginRight: 12, color: '#9b59b6', fontSize: 20 }} />
          <h3 style={{ margin: 0, color: '#2c3e50' }}>AWS Bedrock AI Insights</h3>
        </div>
        <div>Loading Bedrock status...</div>
      </div>
    );
  }

  return (
    <div style={{
      background: '#fff',
      borderRadius: 12,
      padding: 24,
      boxShadow: '0 2px 8px #0001',
      marginBottom: 24
    }}>
      {/* Header with status and toggle */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 20
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <FaBrain style={{ 
            marginRight: 12, 
            color: bedrockStatus.enabled ? '#9b59b6' : '#95a5a6', 
            fontSize: 20 
          }} />
          <h3 style={{ margin: 0, color: '#2c3e50' }}>AWS Bedrock AI Insights</h3>
          <div style={{
            marginLeft: 12,
            padding: '4px 8px',
            borderRadius: 4,
            fontSize: 12,
            fontWeight: 'bold',
            background: bedrockStatus.enabled ? '#e8f5e8' : '#fdf2e9',
            color: bedrockStatus.enabled ? '#27ae60' : '#e67e22'
          }}>
            {bedrockStatus.enabled ? 'ENABLED' : 'DISABLED'}
          </div>
        </div>

        <button
          onClick={toggleBedrock}
          style={{
            padding: '8px 16px',
            border: 'none',
            borderRadius: 6,
            background: bedrockStatus.enabled ? '#e74c3c' : '#27ae60',
            color: '#fff',
            cursor: 'pointer',
            fontSize: 14,
            fontWeight: 500
          }}
        >
          {bedrockStatus.enabled ? 'Disable AI' : 'Enable AI'}
        </button>
      </div>

      {error && (
        <div style={{
          background: '#fee',
          color: '#e74c3c',
          padding: 12,
          borderRadius: 6,
          marginBottom: 16,
          fontSize: 14
        }}>
          {error}
        </div>
      )}

      {/* Status Information */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: 12,
        marginBottom: 20
      }}>
        <div style={{
          background: '#f8f9fa',
          padding: 12,
          borderRadius: 6,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 12, color: '#7f8c8d', marginBottom: 4 }}>Region</div>
          <div style={{ fontWeight: 'bold', color: '#2c3e50' }}>
            {bedrockStatus.region || 'N/A'}
          </div>
        </div>

        <div style={{
          background: '#f8f9fa',
          padding: 12,
          borderRadius: 6,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 12, color: '#7f8c8d', marginBottom: 4 }}>Status</div>
          <div style={{ 
            fontWeight: 'bold', 
            color: bedrockStatus.available ? '#27ae60' : '#e74c3c' 
          }}>
            {bedrockStatus.available ? 'Available' : 'Unavailable'}
          </div>
        </div>

        <div style={{
          background: '#f8f9fa',
          padding: 12,
          borderRadius: 6,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 12, color: '#7f8c8d', marginBottom: 4 }}>Analyzed Logs</div>
          <div style={{ fontWeight: 'bold', color: '#2c3e50' }}>
            {insights.total_logs_analyzed || 0}
          </div>
        </div>
      </div>

      {/* AI Predictions */}
      {bedrockStatus.enabled && bedrockStatus.available && (
        <>
          {predictions.risk_level && (
            <div style={{
              background: '#f8f9fa',
              borderLeft: `4px solid ${getRiskLevelColor(predictions.risk_level)}`,
              padding: 16,
              borderRadius: 6,
              marginBottom: 20
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: 12
              }}>
                <FaChartLine style={{
                  marginRight: 8,
                  color: getRiskLevelColor(predictions.risk_level)
                }} />
                <h4 style={{ margin: 0, color: '#2c3e50' }}>AI Risk Assessment</h4>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: 12
              }}>
                <span style={{ marginRight: 12, color: '#7f8c8d' }}>Risk Level:</span>
                <span style={{
                  fontWeight: 'bold',
                  color: getRiskLevelColor(predictions.risk_level),
                  textTransform: 'uppercase'
                }}>
                  {predictions.risk_level}
                </span>
                <span style={{
                  marginLeft: 12,
                  fontSize: 12,
                  color: '#7f8c8d'
                }}>
                  (Confidence: {predictions.confidence}%)
                </span>
              </div>

              {predictions.predicted_issues && predictions.predicted_issues.length > 0 && (
                <div>
                  <div style={{ 
                    fontSize: 14, 
                    fontWeight: 'bold', 
                    color: '#2c3e50',
                    marginBottom: 8 
                  }}>
                    Predicted Issues:
                  </div>
                  {predictions.predicted_issues.map((issue, index) => (
                    <div key={index} style={{
                      display: 'flex',
                      alignItems: 'center',
                      marginBottom: 4,
                      fontSize: 14
                    }}>
                      <FaExclamationTriangle style={{
                        marginRight: 8,
                        color: '#f39c12',
                        fontSize: 12
                      }} />
                      <span style={{ color: '#2c3e50' }}>
                        {issue.description} ({issue.probability}% probability)
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {predictions.preventive_actions && predictions.preventive_actions.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ 
                    fontSize: 14, 
                    fontWeight: 'bold', 
                    color: '#2c3e50',
                    marginBottom: 8 
                  }}>
                    Recommended Actions:
                  </div>
                  {predictions.preventive_actions.map((action, index) => (
                    <div key={index} style={{
                      fontSize: 14,
                      color: '#27ae60',
                      marginBottom: 4,
                      paddingLeft: 16
                    }}>
                      • {action}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Log Pattern Insights */}
          {insights.classification && insights.classification.patterns && (
            <div style={{
              background: '#f8f9fa',
              padding: 16,
              borderRadius: 6,
              marginBottom: 16
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: 12
              }}>
                <FaRobot style={{ marginRight: 8, color: '#3498db' }} />
                <h4 style={{ margin: 0, color: '#2c3e50' }}>AI Pattern Analysis</h4>
              </div>

              {insights.classification.patterns.slice(0, 3).map((pattern, index) => (
                <div key={index} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 8,
                  padding: '8px 12px',
                  background: '#fff',
                  borderRadius: 4
                }}>
                  <span style={{ color: '#2c3e50', fontSize: 14 }}>
                    {pattern.name}
                  </span>
                  <span style={{
                    background: '#3498db',
                    color: '#fff',
                    padding: '2px 8px',
                    borderRadius: 12,
                    fontSize: 12
                  }}>
                    {pattern.frequency}x
                  </span>
                </div>
              ))}

              {insights.classification.trends && insights.classification.trends.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ 
                    fontSize: 14, 
                    fontWeight: 'bold', 
                    color: '#2c3e50',
                    marginBottom: 8 
                  }}>
                    Key Trends:
                  </div>
                  {insights.classification.trends.slice(0, 2).map((trend, index) => (
                    <div key={index} style={{
                      fontSize: 14,
                      color: '#7f8c8d',
                      marginBottom: 4,
                      fontStyle: 'italic'
                    }}>
                      "{trend}"
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Setup Instructions */}
      {!bedrockStatus.available && (
        <div style={{
          background: '#fff3cd',
          border: '1px solid #ffeaa7',
          borderRadius: 6,
          padding: 16,
          marginTop: 16
        }}>
          <h5 style={{ margin: '0 0 8px 0', color: '#856404' }}>
            AWS Bedrock Setup Required
          </h5>
          <div style={{ fontSize: 14, color: '#856404', lineHeight: 1.5 }}>
            To enable AI-powered log analysis:
            <br />
            1. Configure AWS credentials (aws configure)
            <br />
            2. Enable Bedrock model access in AWS Console
            <br />
            3. Ensure proper IAM permissions for Bedrock
          </div>
        </div>
      )}
    </div>
  );
}

export default BedrockInsights;
