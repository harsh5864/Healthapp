import { useEffect, useState } from 'react';
import { foodApi, wellnessApi } from '../services/appServices';

export default function HistoryPage() {
  const [foods, setFoods] = useState([]);
  const [wellness, setWellness] = useState([]);

  useEffect(() => {
    Promise.all([foodApi.history(), wellnessApi.history()]).then(([f, w]) => {
      setFoods(f.data);
      setWellness(w.data);
    });
  }, []);

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <p className="eyebrow">◷ Your history</p>
          <h1>A record of your check-ins.</h1>
          <p>Only you can access these entries.</p>
        </div>
      </div>
      <div className="history-grid">
        <div className="history-card">
          <h2>Food scans</h2>
          {foods.length ? (
            foods.map((f) => {
              const isPacked = f.scanType === 'PACKED_FOOD' || f.grade;
              return (
                <div className="history-row" key={f.id}>
                  <span>{isPacked ? '📦' : '🍎'}</span>
                  <div>
                    <b>{f.foodName}</b>
                    <small>
                      {f.condition} · {new Date(f.createdAt).toLocaleDateString()}
                    </small>
                  </div>
                  <strong style={{ color: isPacked && f.grade === 'A' ? '#059669' : isPacked && f.grade === 'F' ? '#dc2626' : '#087b6c' }}>
                    {isPacked && f.grade ? `Grade ${f.grade}` : `${f.freshnessScore}%`}
                  </strong>
                </div>
              );
            })
          ) : (
            <div className="empty-state">No food scans yet.</div>
          )}
        </div>
        <div className="history-card">
          <h2>Wellness entries</h2>
          {wellness.length ? (
            wellness.slice(0, 10).map((e) => (
              <div className="history-row" key={e.id}>
                <span>🧠</span>
                <div>
                  <b>Mood {e.mood}/10</b>
                  <small>
                    Stress {e.stress} · Sleep {e.sleepHours}h · {new Date(e.createdAt).toLocaleDateString()}
                  </small>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">No check-ins yet.</div>
          )}
        </div>
      </div>
    </section>
  );
}
