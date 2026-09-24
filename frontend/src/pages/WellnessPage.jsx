import { useEffect, useState } from 'react';
import { wellnessApi } from '../services/appServices';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export default function WellnessPage() {
  const [form, setForm] = useState({
    mood: 7,
    stress: 4,
    energy: 7,
    activity: 6,
    sleepHours: 7.5,
    journalText: ''
  });
  const [summary, setSummary] = useState(null);
  const [notice, setNotice] = useState('');
  const [loadingAction, setLoadingAction] = useState('');

  const load = () => {
    wellnessApi.summary().then((r) => setSummary(r.data)).catch(() => {});
  };

  useEffect(load, []);

  const submit = async (e) => {
    e.preventDefault();
    try {
      await wellnessApi.checkIn({
        mood: Number(form.mood),
        stress: Number(form.stress),
        energy: Number(form.energy),
        activity: Number(form.activity),
        sleepHours: Number(form.sleepHours),
        journalText: form.journalText
      });
      setNotice('Check-in and multi-pillar AI analysis saved.');
      setForm({ ...form, journalText: '' });
      load();
    } catch {
      setNotice('Unable to save check-in. Please try again.');
    }
  };

  const handleRefreshSleepLm = async () => {
    setLoadingAction('sleeplm');
    try {
      const res = await wellnessApi.sleepLm();
      setSummary((prev) => ({ ...prev, sleepLm: res.data }));
    } catch {}
    setLoadingAction('');
  };

  const handleRefreshMenta = async () => {
    setLoadingAction('menta');
    try {
      const res = await wellnessApi.menta();
      setSummary((prev) => ({ ...prev, menta: res.data }));
    } catch {}
    setLoadingAction('');
  };

  const handleRefreshObservation = async () => {
    setLoadingAction('observation');
    try {
      const res = await wellnessApi.trends();
      setSummary((prev) => ({ ...prev, analysis: res.data, sleepLm: res.data?.sleepLm || prev?.sleepLm, menta: res.data?.menta || prev?.menta }));
    } catch {}
    setLoadingAction('');
  };

  const chartData = [...(summary?.entries || [])].reverse().map((e) => ({
    date: new Date(e.createdAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    mood: e.mood,
    stress: e.stress,
    energy: e.energy,
    activity: e.activity || 5,
    sleep: e.sleepHours
  }));

  const sleepLm = summary?.sleepLm || summary?.analysis?.sleepLm;
  const menta = summary?.menta || summary?.analysis?.menta;

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <p className="eyebrow">🧠 Multi-Pillar Wellness</p>
          <h1>Mind, Body & Sleep Intelligence.</h1>
          <p>Powered by SleepLM for clinical sleep summaries and Menta for mood, energy, activity & stress synthesis.</p>
        </div>
      </div>

      <div className="wellness-layout">
        {/* Daily Check-In Form */}
        <form className="checkin-card" onSubmit={submit}>
          <h2>Daily check-in</h2>

          <Range label="Mood" value={form.mood} onChange={(v) => setForm({ ...form, mood: v })} color="green" />
          <Range label="Energy" value={form.energy} onChange={(v) => setForm({ ...form, energy: v })} color="blue" />
          <Range label="Activity & Movement" value={form.activity} onChange={(v) => setForm({ ...form, activity: v })} color="purple" />
          <Range label="Stress" value={form.stress} onChange={(v) => setForm({ ...form, stress: v })} color="orange" />

          <label>
            Sleep duration (hours)
            <input
              type="number"
              min="0"
              max="24"
              step="0.1"
              value={form.sleepHours}
              onChange={(e) => setForm({ ...form, sleepHours: e.target.value })}
            />
          </label>

          <label>
            Optional journal
            <textarea
              rows="3"
              maxLength="5000"
              value={form.journalText}
              onChange={(e) => setForm({ ...form, journalText: e.target.value })}
              placeholder="Reflections on sleep quality, thoughts, or physical activity today..."
            />
          </label>

          <button className="button button--primary full">Save check-in</button>
          {notice && <p className="success-note">{notice}</p>}
        </form>

        {/* Intelligence & Analytics Column */}
        <div>
          {/* Top Metric Bar */}
          <div className="trend-card">
            <div className="section-title">
              <h2>Vitality Metrics</h2>
              <button
                className="text-button"
                onClick={handleRefreshObservation}
                disabled={loadingAction === 'observation'}
              >
                {loadingAction === 'observation' ? 'Analyzing…' : '↻ Refresh AI Observation'}
              </button>
            </div>

            <div className="trend-metrics" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
              <Metric label="Mood" value={summary?.averageMood ? `${summary.averageMood}/10` : '—'} />
              <Metric label="Energy" value={summary?.averageEnergy ? `${summary.averageEnergy}/10` : '—'} />
              <Metric label="Activity" value={summary?.averageActivity ? `${summary.averageActivity}/10` : '—'} />
              <Metric label="Stress" value={summary?.averageStress ? `${summary.averageStress}/10` : '—'} />
              <Metric label="Sleep" value={summary?.averageSleep ? `${summary.averageSleep}h` : '—'} />
            </div>

            {/* Recharts Multi-Pillar Trend Chart */}
            <div className="chart-card">
              <h3>Mood, Energy, Activity & Stress Trends</h3>
              {chartData.length ? (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={chartData}>
                    <CartesianGrid stroke="#e8f0eb" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#789188' }} />
                    <YAxis domain={[1, 10]} tick={{ fontSize: 11, fill: '#789188' }} />
                    <Tooltip />
                    <Line type="monotone" name="Mood" dataKey="mood" stroke="#168d74" strokeWidth={3} dot={{ r: 3 }} />
                    <Line type="monotone" name="Energy" dataKey="energy" stroke="#6197bb" strokeWidth={2} dot={{ r: 3 }} />
                    <Line type="monotone" name="Activity" dataKey="activity" stroke="#7e22ce" strokeWidth={2} dot={{ r: 3 }} />
                    <Line type="monotone" name="Stress" dataKey="stress" stroke="#dc9760" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state">Save your first check-in to see your multi-pillar chart.</div>
              )}
            </div>
          </div>

          {/* SleepLM API Module Card */}
          <div className="ai-module-card ai-module-card--sleeplm">
            <div className="ai-module-header">
              <div className="ai-module-brand">
                <div className="ai-module-icon ai-module-icon--sleeplm">☾</div>
                <div>
                  <h3 className="ai-module-title">
                    SleepLM API
                    <span className="ai-module-tag ai-module-tag--sleeplm">Circadian Engine</span>
                  </h3>
                  <p className="ai-module-sub">Sleep Architecture, Recovery & Rhythm Intelligence</p>
                </div>
              </div>
              <button
                className="text-button"
                onClick={handleRefreshSleepLm}
                disabled={loadingAction === 'sleeplm'}
              >
                {loadingAction === 'sleeplm' ? 'Analyzing Sleep…' : '↻ Refresh SleepLM'}
              </button>
            </div>

            {sleepLm ? (
              <>
                <div className="ai-badge-row">
                  <div className="ai-metric-pill">
                    <small>Sleep Score</small>
                    <strong className="score-highlight--purple">{sleepLm.sleepScore ?? 85}/100</strong>
                  </div>
                  <div className="ai-metric-pill">
                    <small>Sleep Debt</small>
                    <strong>{sleepLm.sleepDebt || 'Optimal'}</strong>
                  </div>
                  <div className="ai-metric-pill">
                    <small>Schedule</small>
                    <strong>{sleepLm.sleepConsistency || 'Consistent'}</strong>
                  </div>
                  <div className="ai-metric-pill">
                    <small>Restoration</small>
                    <strong>{sleepLm.restorativeQuality || 'Deep Rest'}</strong>
                  </div>
                </div>

                <div className="ai-summary-text">
                  <b>SleepLM Clinical Synthesis:</b>
                  <p style={{ margin: '6px 0 0', whiteSpace: 'pre-line' }}>{sleepLm.sleepSummary}</p>
                </div>

                {sleepLm.recommendations?.length > 0 && (
                  <div>
                    <b style={{ fontSize: '0.76rem', color: '#31584d' }}>Restorative Sleep Hygiene Guidance:</b>
                    <ul className="ai-rec-list">
                      {sleepLm.recommendations.map((rec, i) => (
                        <li key={i} className="ai-rec-item">
                          <span>✓</span>
                          <div>{rec}</div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="empty-state">Log a check-in with your sleep duration to trigger SleepLM analysis.</div>
            )}
          </div>

          {/* Menta API Module Card */}
          <div className="ai-module-card ai-module-card--menta">
            <div className="ai-module-header">
              <div className="ai-module-brand">
                <div className="ai-module-icon ai-module-icon--menta">🧠</div>
                <div>
                  <h3 className="ai-module-title">
                    Menta API
                    <span className="ai-module-tag ai-module-tag--menta">Mind-Body Engine</span>
                  </h3>
                  <p className="ai-module-sub">Holistic Mood, Energy, Activity & Stress Equilibrium</p>
                </div>
              </div>
              <button
                className="text-button"
                onClick={handleRefreshMenta}
                disabled={loadingAction === 'menta'}
              >
                {loadingAction === 'menta' ? 'Analyzing Menta…' : '↻ Refresh Menta'}
              </button>
            </div>

            {menta ? (
              <>
                <div className="ai-badge-row">
                  <div className="ai-metric-pill">
                    <small>Menta Vitality Index</small>
                    <strong className="score-highlight">{menta.wellnessScore ?? 80}/100</strong>
                  </div>
                  <div className="ai-metric-pill">
                    <small>Mood State</small>
                    <strong>{menta.moodState || 'Balanced'}</strong>
                  </div>
                  <div className="ai-metric-pill">
                    <small>Energy Level</small>
                    <strong>{menta.energyLevel || 'Steady'}</strong>
                  </div>
                  <div className="ai-metric-pill">
                    <small>Stress Load</small>
                    <strong>{menta.stressLevel || 'Manageable'}</strong>
                  </div>
                </div>

                <div className="ai-summary-text">
                  <b>Menta Multi-Pillar Synthesis:</b>
                  <p style={{ margin: '6px 0 0', whiteSpace: 'pre-line' }}>{menta.mentaSummary}</p>
                </div>

                {menta.mindfulnessAction && (
                  <div className="menta-action-box">
                    <span>✦</span>
                    <div>
                      <b>Menta Somatic Micro-Action:</b>
                      <p>{menta.mindfulnessAction}</p>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="empty-state">Log a check-in to generate a personalized Menta mind-body synthesis.</div>
            )}
          </div>

          {/* Recent Entries Strip */}
          <div className="history-mini">
            <h3>Recent entries</h3>
            {summary?.entries?.slice(0, 5).map((e) => (
              <div key={e.id}>
                <span>{new Date(e.createdAt).toLocaleDateString()}</span>
                <b>Mood {e.mood}/10</b>
                <b>Activity {e.activity || 5}/10</b>
                <b>Sleep {e.sleepHours}h</b>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Range({ label, value, onChange, color }) {
  return (
    <label className="range-label">
      <span>
        <b>{label}</b>
        <strong>{value}/10</strong>
      </span>
      <input
        className={`range range--${color}`}
        type="range"
        min="1"
        max="10"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}
