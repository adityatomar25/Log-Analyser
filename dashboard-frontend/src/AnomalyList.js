import React, { useState, useEffect } from 'react';
import config from './config';
import './App.css';

function AnomalyList({ sourceKey }) {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setAnomalies([]); // Reset anomalies on source change
    setLoading(true);
    const interval = setInterval(() => {
      fetch(`${config.API_BASE_URL}/api/anomalies`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
          setAnomalies(data.anomalies || []);
          setLoading(false);
        })
        .catch(() => {
          setAnomalies([]);
          setLoading(false);
        });
    }, 2000);
    return () => clearInterval(interval);
  }, [sourceKey]);

  return (
    <div className="card">
      <h2>Anomalies</h2>
      {loading ? <div>Waiting for anomalies...</div> :
        anomalies.length === 0 ? <div>No anomalies detected</div> :
        <ul style={{paddingLeft: 18, margin: 0}}>
          {anomalies.map((a, idx) => (
            <li key={idx} style={{color: '#e74c3c', fontWeight: 600, marginBottom: 6, fontSize: 15, background: '#fff6f6', borderRadius: 8, padding: '6px 10px', boxShadow: '0 1px 4px #e74c3c22'}}>
              <span role="img" aria-label="alert" style={{marginRight: 8}}>⚠️</span>{a}
            </li>
          ))}
        </ul>
      }
    </div>
  );
}
export default AnomalyList;