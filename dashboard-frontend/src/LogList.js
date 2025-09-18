import React, { useState, useEffect } from 'react';
import './App.css';
import { FaBug, FaExclamationTriangle, FaInfoCircle, FaCheckCircle, FaTrashAlt } from 'react-icons/fa';

function parseLogMessage(log) {
  try {
    const msgObj = JSON.parse(log.message);
    if (msgObj && msgObj.message && msgObj.level) {
      return {
        text: msgObj.message,
        level: msgObj.level,
        user: msgObj.user_id,
        service: msgObj.service_id,
        raw: msgObj
      };
    }
  } catch {
    // Not JSON, fall back to plain text
  }
  // Try to extract user/service from plain text
  const userMatch = log.message.match(/\[(user\d+)\]/);
  const serviceMatch = log.message.match(/\[(svc-[^\]]+)\]/);
  return {
    text: log.message,
    level: log.level,
    user: log.user_id || (userMatch ? userMatch[1] : ''),
    service: log.service_id || (serviceMatch ? serviceMatch[1] : ''),
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

  useEffect(() => {
    setLogs([]); // Reset logs on source change
    setLoading(true);
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
    const fetchLogs = () => {
      fetch(`http://localhost:8000/api/db_logs?${params.toString()}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
          setLogs(Array.isArray(data) ? data : []);
          setLoading(false);
        })
        .catch(() => {
          setLogs([]);
          setLoading(false);
        });
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [sourceKey, search]);

  const safeLogs = Array.isArray(logs) ? logs : [];
  const filteredLogs = safeLogs.map(parseLogMessage);

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

  return (
    <div className="card">
      <h2>Recent Logs</h2>
      {loading ? <div>Waiting for logs...</div> :
        filteredLogs.length === 0 ? <div>No logs available.</div> :
        filteredLogs.map((log, idx) => (
          <div key={idx} className="log-entry">
            <span>
              <span className={`log-level ${log.level}`}>{levelIcon[log.level] || null}{log.level}</span>
              {log.text}
              {log.user && <span style={{marginLeft: 8, color: '#888'}}>User: {log.user}</span>}
              {log.service && <span style={{marginLeft: 8, color: '#888'}}>Service: {log.service}</span>}
            </span>
            {role === 'admin' && safeLogs[idx] && safeLogs[idx].id && (
              <button style={{marginLeft: 12}} className="button-primary" onClick={() => handleDelete(safeLogs[idx].id)} title="Delete log">
                <FaTrashAlt style={{marginRight: 4}} />Delete
              </button>
            )}
          </div>
        ))
      }
    </div>
  );
}
export default LogList;