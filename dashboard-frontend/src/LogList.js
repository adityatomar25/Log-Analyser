import React, { useState, useEffect } from 'react';

function parseLogMessage(log) {
  try {
    const msgObj = JSON.parse(log.message);
    if (msgObj && msgObj.message && msgObj.level) {
      return {
        text: `[${msgObj.level}] ${msgObj.message} (${msgObj.user_id}, ${msgObj.service_id}, ${msgObj.request_id})`,
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
    text: `[${log.level}] ${log.message}`,
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

function LogList({ sourceKey, search }) {
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

  return (
    <div>
      <h2>Recent Logs</h2>
      {loading ? <div>Waiting for logs...</div> :
        filteredLogs.length === 0 ? <div>No logs available.</div> :
        filteredLogs.map((log, idx) => (
          <div key={idx}>{log.text}</div>
        ))
      }
    </div>
  );
}
export default LogList;