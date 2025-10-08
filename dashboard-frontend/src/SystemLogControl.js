import React, { useState, useEffect } from 'react';
import config from './config';

function SystemLogControl() {
  const [systemLogStatus, setSystemLogStatus] = useState({
    enabled: false,
    running: false
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Fetch current system log status
  useEffect(() => {
    fetchSystemLogStatus();
    // Poll status every 5 seconds
    const interval = setInterval(fetchSystemLogStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSystemLogStatus = () => {
    fetch(`${config.API_BASE_URL}/api/system_logs/status`, { 
      credentials: 'include' 
    })
      .then(res => res.json())
      .then(data => {
        setSystemLogStatus(data);
      })
      .catch(err => {
        console.error('Failed to fetch system log status:', err);
      });
  };

  const toggleSystemLogs = () => {
    setLoading(true);
    const newEnabled = !systemLogStatus.enabled;
    
    fetch(`${config.API_BASE_URL}/api/system_logs/toggle`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: newEnabled })
    })
      .then(res => res.json())
      .then(data => {
        setSystemLogStatus(data);
        setMessage(data.message);
        setTimeout(() => setMessage(''), 3000); // Clear message after 3 seconds
      })
      .catch(err => {
        console.error('Failed to toggle system logs:', err);
        setMessage('Failed to toggle system logs');
        setTimeout(() => setMessage(''), 3000);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div style={{
      background: '#fff',
      borderRadius: 16,
      padding: 20,
      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
      marginBottom: 24,
      border: '1px solid #e1e8ed'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ 
            margin: 0, 
            marginBottom: 8,
            color: '#2c3e50',
            fontSize: 18,
            fontWeight: 600
          }}>
            🖥️ System Log Collection
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{
              fontSize: 14,
              color: systemLogStatus.enabled ? '#27ae60' : '#7f8c8d',
              fontWeight: 500
            }}>
              Status: {systemLogStatus.enabled ? 'Enabled' : 'Disabled'}
            </span>
            <span style={{
              fontSize: 12,
              padding: '4px 8px',
              borderRadius: 12,
              background: systemLogStatus.running ? '#d5f4e6' : '#ffeaea',
              color: systemLogStatus.running ? '#27ae60' : '#e74c3c',
              fontWeight: 500
            }}>
              {systemLogStatus.running ? '🟢 Running' : '🔴 Stopped'}
            </span>
          </div>
        </div>
        
        <button
          onClick={toggleSystemLogs}
          disabled={loading}
          style={{
            padding: '10px 20px',
            border: 'none',
            borderRadius: 8,
            background: systemLogStatus.enabled ? '#e74c3c' : '#27ae60',
            color: 'white',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1,
            transition: 'all 0.3s ease'
          }}
        >
          {loading ? '...' : (systemLogStatus.enabled ? 'Stop' : 'Start')} System Logs
        </button>
      </div>
      
      {message && (
        <div style={{
          marginTop: 12,
          padding: '8px 12px',
          background: '#e8f5e8',
          color: '#27ae60',
          borderRadius: 6,
          fontSize: 14,
          fontWeight: 500
        }}>
          {message}
        </div>
      )}
      
      <div style={{
        marginTop: 12,
        fontSize: 12,
        color: '#7f8c8d',
        lineHeight: 1.4
      }}>
        System log collection tails macOS system logs from /var/log/system.log and integrates them with your application logs for comprehensive monitoring.
      </div>
    </div>
  );
}

export default SystemLogControl;
