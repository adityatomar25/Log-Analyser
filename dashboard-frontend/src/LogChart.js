import React, { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import './App.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function LogChart({ sourceKey }) {
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setCounts({}); // Reset chart on source change
    setLoading(true);
    const interval = setInterval(() => {
      fetch('http://localhost:8000/api/anomalies', { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
          setCounts(data.counts || {});
          setLoading(false);
        })
        .catch(() => {
          setCounts({});
          setLoading(false);
        });
    }, 2000);
    return () => clearInterval(interval);
  }, [sourceKey]);
  const data = {
    labels: Object.keys(counts),
    datasets: [{
      label: 'Log Levels',
      data: Object.values(counts),
      backgroundColor: ['#2980b9', '#f39c12', '#e74c3c', '#8e44ad', '#16a085'],
      borderRadius: 8,
      barPercentage: 0.6,
      categoryPercentage: 0.6
    }]
  };
  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'top', labels: { font: { size: 15, family: 'Inter, Segoe UI, Arial, sans-serif' } } },
      title: { display: true, text: 'Log Level Counts (Last 60s)', font: { size: 18, weight: 'bold', family: 'Inter, Segoe UI, Arial, sans-serif' } }
    },
    scales: {
      x: { ticks: { font: { size: 14, family: 'Inter, Segoe UI, Arial, sans-serif' } } },
      y: { beginAtZero: true, ticks: { font: { size: 14, family: 'Inter, Segoe UI, Arial, sans-serif' } } }
    }
  };
  return (
    <div className="card">
      {loading ? <div>Waiting for chart data...</div> : <Bar data={data} options={options} />}
    </div>
  );
}

export default LogChart;