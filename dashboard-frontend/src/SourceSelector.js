import React, { useState, useEffect } from 'react';
import config from './config';

function SourceSelector({ onSourceChange }) {
  const [source, setSource] = useState('local');
  const [group, setGroup] = useState('');
  const [stream, setStream] = useState('');
  const [region, setRegion] = useState('us-east-1');
  const [apiUrl, setApiUrl] = useState('');

  // Fetch current source from backend on mount
  useEffect(() => {
    fetch(`${config.API_BASE_URL}/api/source`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data && data.type) {
          setSource(data.type);
          setGroup(data.group || '');
          setStream(data.stream || '');
          setRegion(data.region || 'us-east-1');
          setApiUrl(data.api_url || '');
        }
      });
  }, []);

  const handleSwitch = async () => {
    let data = { type: source };
    if (source === 'cloudwatch') {
      data.group = group;
      data.stream = stream;
      data.region = region;
    } else if (source === 'api') {
      data.api_url = apiUrl;
    }
    await fetch(`${config.API_BASE_URL}/api/source`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (onSourceChange) onSourceChange(source);
  };

  return (
    <div style={{marginBottom: 20}}>
      <label style={{marginRight: 10}}>Log Source:</label>
      <select value={source} onChange={e => setSource(e.target.value)}>
        <option value="local">Local</option>
        <option value="cloudwatch">CloudWatch</option>
        <option value="api">API</option>
      </select>
      {source === 'cloudwatch' && (
        <span>
          <input placeholder="Log Group" value={group} onChange={e => setGroup(e.target.value)} style={{marginLeft: 10}} />
          <input placeholder="Log Stream (optional)" value={stream} onChange={e => setStream(e.target.value)} style={{marginLeft: 10}} />
          <input placeholder="Region" value={region} onChange={e => setRegion(e.target.value)} style={{marginLeft: 10, width: 100}} />
        </span>
      )}
      {source === 'api' && (
        <input placeholder="API URL" value={apiUrl} onChange={e => setApiUrl(e.target.value)} style={{marginLeft: 10, width: 300}} />
      )}
      <button onClick={handleSwitch} style={{marginLeft: 10}}>Switch</button>
    </div>
  );
}

export default SourceSelector;
