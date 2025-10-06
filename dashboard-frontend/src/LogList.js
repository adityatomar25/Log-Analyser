import React, { useState, useEffect } from 'react';
import './App.css';
import { FaBug, FaExclamationTriangle, FaInfoCircle, FaCheckCircle, FaTrashAlt } from 'react-icons/fa';

function parseLogMessage(log) {
  // Check if it's a system log
  const isSystemLog = log.log_type === 'system' || (log.source && log.source.includes('system'));
  
  try {
    const msgObj = JSON.parse(log.message);
    if (msgObj && msgObj.message && msgObj.level) {
      return {
        text: msgObj.message,
        level: msgObj.level,
        user: msgObj.user_id,
        service: msgObj.service_id,
        isSystemLog: isSystemLog,
        hostname: msgObj.hostname,
        raw: msgObj
      };
    }
  } catch {
    // Not JSON, fall back to plain text
  }
  
  // For system logs, try to extract hostname and source
  if (isSystemLog) {
    return {
      text: log.message,
      level: log.level,
      user: log.user_id || '',
      service: log.service_id || log.source || '',
      isSystemLog: true,
      hostname: log.hostname || 'Unknown',
      raw: log
    };
  }
  
  // Try to extract user/service from plain text
  const userMatch = log.message.match(/\[(user\d+)\]/);
  const serviceMatch = log.message.match(/\[(svc-[^\]]+)\]/);
  return {
    text: log.message,
    level: log.level,
    user: log.user_id || (userMatch ? userMatch[1] : ''),
    service: log.service_id || (serviceMatch ? serviceMatch[1] : ''),
    isSystemLog: false,
    raw: log
  };
}

function toUnixTimestamp(dtStr) {
  if (!dtStr) return undefined;
  return Math.floor(new Date(dtStr).getTime() / 1000);
}

const levelIcon = {
  'ERROR': <FaExclamationTriangle style={{color: '#e74c3c', marginRight: 4}} title="Error" />,
  'CRITICAL': <FaBug style={{color: '#c0392b', marginRight: 4}} title="Critical" />,
  'WARN': <FaExclamationTriangle style={{color: '#f39c12', marginRight: 4}} title="Warning" />,
  'INFO': <FaInfoCircle style={{color: '#2980b9', marginRight: 4}} title="Info" />,
  'DEBUG': <FaCheckCircle style={{color: '#16a085', marginRight: 4}} title="Debug" />
};

function LogList({ sourceKey, search, role }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  // Debug: Track last fetched raw logs and parsed logs
  useEffect(() => {
    if (logs && logs.length > 0) {
      // Print raw logs
      // eslint-disable-next-line no-console
      console.log('[LogList] Raw logs from API:', logs);
    }
  }, [logs]);

  // Skeleton loader component
  const SkeletonLoader = () => (
    <div className="log-card">
      <div className="card-header">
        <h3 className="card-title">📋 Recent Logs</h3>
        <div className="status-indicator status-success" style={{opacity: 0.5}}>
          Loading...
        </div>
      </div>
      {[...Array(5)].map((_, i) => (
        <div key={i} style={{
          height: 60,
          background: 'rgba(255, 255, 255, 0.1)',
          borderRadius: 12,
          marginBottom: 12,
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            left: '-100%',
            width: '100%',
            height: '100%',
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
            animation: `shimmer 1.5s infinite ${i * 0.2}s`
          }}></div>
        </div>
      ))}
    </div>
  );

  // Error component
  const ErrorComponent = () => (
    <div className="log-card" style={{textAlign: 'center', padding: 40}}>
      <div style={{fontSize: 48, marginBottom: 16}}>⚠️</div>
      <h3 style={{color: 'white', marginBottom: 16}}>Unable to Load Logs</h3>
      <p style={{color: 'rgba(255,255,255,0.8)', marginBottom: 24}}>
        {error || 'Something went wrong while fetching logs.'}
      </p>
      <button
        onClick={() => {
          setError(null);
          setRetryCount(prev => prev + 1);
        }}
        className="btn-modern"
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '12px 24px',
          borderRadius: 12,
          color: 'white',
          border: 'none',
          fontWeight: 600,
          cursor: 'pointer'
        }}
      >
        🔄 Retry ({retryCount + 1})
      </button>
    </div>
  );

  useEffect(() => {
    setLogs([]); // Reset logs on source change
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (search) {
      if (search.level) params.append('level', search.level);
      if (search.user) params.append('user_id', search.user);
      if (search.service) params.append('service_id', search.service);
      if (search.keyword) params.append('keyword', search.keyword);
      if (search.startTime) {
        const ts = toUnixTimestamp(search.startTime);
        if (ts) params.append('start_time', ts);
      }
      if (search.endTime) {
        const ts = toUnixTimestamp(search.endTime);
        if (ts) params.append('end_time', ts);
      }
    }
    params.append('limit', 50);
    const fetchLogs = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/db_logs?${params.toString()}`, { 
          credentials: 'include',
          signal: AbortSignal.timeout(10000) // 10 second timeout
        });
        
        if (!res.ok) {
          throw new Error(`Server error: ${res.status} ${res.statusText}`);
        }
        
        const data = await res.json();
        setLogs(Array.isArray(data) ? data : []);
        setLoading(false);
        setError(null);
        
      } catch (err) {
        console.error('[LogList] Error fetching logs:', err);
        
        if (err.name === 'TimeoutError') {
          setError('Request timed out. Please check your connection.');
        } else if (err.message.includes('401')) {
          setError('Authentication required. Please log in again.');
        } else if (err.message.includes('500')) {
          setError('Server error. Please try again later.');
        } else {
          setError('Unable to load logs. Check your connection.');
        }
        
        setLogs([]);
        setLoading(false);
      }
    };
    fetchLogs();
    // Reduce polling frequency and add exponential backoff on errors
    const pollInterval = error ? Math.min(5000 * Math.pow(1.5, retryCount), 30000) : 5000;
    const interval = setInterval(fetchLogs, pollInterval);
    return () => clearInterval(interval);
  }, [sourceKey, search, retryCount, error]);

  const safeLogs = Array.isArray(logs) ? logs : [];
  const filteredLogs = safeLogs.map((log, idx) => {
    const parsed = parseLogMessage(log);
    // Debug: Print each parsed log
    // eslint-disable-next-line no-console
    console.log(`[LogList] Parsed log #${idx}:`, parsed);
    return parsed;
  });

  // Delete log handler
  const handleDelete = async (logId) => {
    if (!window.confirm('Are you sure you want to delete this log?')) return;
    await fetch(`http://localhost:8000/logs/${logId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    // Refresh logs
    setLogs(logs => logs.filter(l => l.id !== logId));
  };

  // Show loading state
  if (loading && logs.length === 0) {
    return <SkeletonLoader />;
  }

  // Show error state
  if (error && logs.length === 0) {
    return <ErrorComponent />;
  }

  return (
    <div className="log-card">
      <div className="card-header">
        <h3 className="card-title">📋 Recent Logs</h3>
        <div className="status-indicator status-success">
          {filteredLogs.length} entries
        </div>
      </div>
      {filteredLogs.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: 40,
          color: 'rgba(255,255,255,0.8)'
        }}>
          <div style={{fontSize: 48, marginBottom: 16}}>📭</div>
          <p>No logs available for the selected criteria.</p>
        </div>
      ) : (
        filteredLogs.map((log, idx) => (
          <div key={idx} className={`log-entry ${log.isSystemLog ? 'system-log' : ''}`} style={{
            borderLeft: log.isSystemLog ? '4px solid #3498db' : undefined,
            background: log.isSystemLog ? 'linear-gradient(90deg, #f8f9fa 0%, #e3f2fd 100%)' : undefined
          }}>
            <span>
              {log.isSystemLog && <span style={{
                background: '#3498db', 
                color: 'white', 
                padding: '2px 6px', 
                borderRadius: '4px', 
                fontSize: '11px', 
                marginRight: '8px',
                fontWeight: 'bold'
              }}>🖥️ SYSTEM</span>}
              <span className={`log-level ${log.level || 'UNKNOWN'}`}>{levelIcon[log.level] || null}{log.level || 'UNKNOWN'}</span>
              {log.text || '[No message]'}
              {log.isSystemLog && log.hostname && <span style={{marginLeft: 8, color: '#666', fontStyle: 'italic'}}>Host: {log.hostname}</span>}
              {!log.isSystemLog && log.user ? <span style={{marginLeft: 8, color: '#888'}}>User: {log.user}</span> : 
               !log.isSystemLog && <span style={{marginLeft: 8, color: '#bbb'}}>User: N/A</span>}
              {log.service ? <span style={{marginLeft: 8, color: '#888'}}>Service: {log.service}</span> : 
               !log.isSystemLog && <span style={{marginLeft: 8, color: '#bbb'}}>Service: N/A</span>}
            </span>
            {role === 'admin' && safeLogs[idx] && safeLogs[idx].id && (
              <button style={{marginLeft: 12}} className="button-primary" onClick={() => handleDelete(safeLogs[idx].id)} title="Delete log">
                <FaTrashAlt style={{marginRight: 4}} />Delete
              </button>
            )}
          </div>
        ))
      )}
    </div>
  );
}
export default LogList;