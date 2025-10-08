import React, { useState } from 'react';
import config from './config';

function toCSV(logs) {
  if (!logs.length) return '';
  const keys = Object.keys(logs[0]);
  const header = keys.join(',');
  const rows = logs.map(log => keys.map(k => `"${(log[k] || '').toString().replace(/"/g, '""')}"`).join(','));
  return [header, ...rows].join('\n');
}

function SearchBar({ onSearch }) {
  const [keyword, setKeyword] = useState('');
  const [level, setLevel] = useState('');
  const [user, setUser] = useState('');
  const [service, setService] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    onSearch({ keyword, level, user, service, startTime, endTime });
  };

  const handleExport = async () => {
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    if (user) params.append('user_id', user);
    if (service) params.append('service_id', service);
    if (keyword) params.append('keyword', keyword);
    if (startTime) params.append('start_time', Math.floor(new Date(startTime).getTime() / 1000));
    if (endTime) params.append('end_time', Math.floor(new Date(endTime).getTime() / 1000));
    params.append('limit', 500); // Export up to 500 logs
    const res = await fetch(`${config.API_BASE_URL}/api/db_logs?${params.toString()}`, { credentials: 'include' });
    const logs = await res.json();
    const csv = toCSV(logs);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'logs.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <form onSubmit={handleSearch} style={{display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center'}}>
      <input type="text" placeholder="Search keyword" value={keyword} onChange={e => setKeyword(e.target.value)} style={{padding: 8, borderRadius: 6, border: '1px solid #b0c4de', minWidth: 140}} />
      <select value={level} onChange={e => setLevel(e.target.value)} style={{padding: 8, borderRadius: 6, border: '1px solid #b0c4de'}}>
        <option value="">All Levels</option>
        <option value="INFO">INFO</option>
        <option value="WARNING">WARNING</option>
        <option value="ERROR">ERROR</option>
        <option value="CRITICAL">CRITICAL</option>
      </select>
      <input type="text" placeholder="User ID" value={user} onChange={e => setUser(e.target.value)} style={{padding: 8, borderRadius: 6, border: '1px solid #b0c4de', minWidth: 100}} />
      <input type="text" placeholder="Service" value={service} onChange={e => setService(e.target.value)} style={{padding: 8, borderRadius: 6, border: '1px solid #b0c4de', minWidth: 100}} />
      <input type="datetime-local" value={startTime} onChange={e => setStartTime(e.target.value)} style={{padding: 8, borderRadius: 6, border: '1px solid #b0c4de'}} />
      <input type="datetime-local" value={endTime} onChange={e => setEndTime(e.target.value)} style={{padding: 8, borderRadius: 6, border: '1px solid #b0c4de'}} />
      <button type="submit" style={{padding: '8px 18px', borderRadius: 6, background: '#2980b9', color: '#fff', border: 'none', fontWeight: 600}}>Search</button>
      <button type="button" onClick={handleExport} style={{padding: '8px 18px', borderRadius: 6, background: '#27ae60', color: '#fff', border: 'none', fontWeight: 600}}>Export CSV</button>
    </form>
  );
}

export default SearchBar;
