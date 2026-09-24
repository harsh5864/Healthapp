import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { dashboardApi, foodApi, wellnessApi } from '../services/appServices';
import { useAuth } from '../context/AuthContext';
import FeatureCard from '../components/FeatureCard';

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [food, setFood] = useState([]);
  const [wellness, setWellness] = useState(null);

  useEffect(() => {
    Promise.all([dashboardApi.summary(), foodApi.history(), wellnessApi.summary()])
      .then(([d, f, w]) => {
        setData(d.data);
        setFood(f.data);
        setWellness(w.data);
      })
      .catch(() => {});
  }, []);

  const sleepLm = data?.sleepLm || wellness?.sleepLm || wellness?.analysis?.sleepLm;
  const menta = data?.menta || wellness?.menta || wellness?.analysis?.menta;

  return (
    <section className="page-content">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Your overview</p>
          <h1>Good to see you, {user?.name?.split(' ')[0] || 'there'}.</h1>
          <p>Real-time mind-body wellness powered by SleepLM, Menta, and clinical AI companion tools.</p>
        </div>
        <Link className="button button--primary" to="/app/wellness">
          Daily check-in <span>→</span>
        </Link>
      </div>

      {/* Top 5 Metrics Bar */}
      <div className="metric-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        <Metric label="Food scans" value={data?.foodScans ?? '—'} icon="🍎" />
        <Metric label="Conversations" value={data?.conversations ?? '—'} icon="✦" />
        <Metric label="Current mood" value={data?.currentMood ? `${data.currentMood}/10` : '—'} icon="◒" />
        <Metric
          label="Sleep (SleepLM)"
          value={data?.averageSleep ? `${Number(data.averageSleep).toFixed(1)}h` : '—'}
          icon="☾"
        />
        <Metric
          label="Activity (Menta)"
          value={data?.averageActivity ? `${Number(data.averageActivity).toFixed(1)}/10` : '—'}
          icon="⚡"
        />
      </div>

      {/* Dual Intelligence Cards: SleepLM & Menta */}
      <div className="overview-ai-grid">
        {/* SleepLM Overview Card */}
        <div className="overview-ai-banner overview-ai-banner--sleeplm">
          <div>
            <div className="overview-banner-top">
              <div className="overview-banner-title">
                <span style={{ fontSize: '1.2rem', color: '#4f46e5' }}>☾</span>
                <span>SleepLM Summary</span>
              </div>
              <div className="overview-banner-score overview-banner-score--purple">
                {sleepLm?.sleepScore ? `${sleepLm.sleepScore}%` : '85%'}
              </div>
            </div>
            <p className="overview-banner-body">
              {sleepLm?.sleepSummary ||
                'SleepLM analyzes your sleep duration, circadian rhythms, and restorative phases for optimal waking energy.'}
            </p>
          </div>
          <Link className="overview-banner-link" to="/app/wellness">
            Open SleepLM intelligence <span>→</span>
          </Link>
        </div>

        {/* Menta Overview Card */}
        <div className="overview-ai-banner overview-ai-banner--menta">
          <div>
            <div className="overview-banner-top">
              <div className="overview-banner-title">
                <span style={{ fontSize: '1.2rem', color: '#059669' }}>🧠</span>
                <span>Menta Mind-Body</span>
              </div>
              <div className="overview-banner-score">
                {menta?.wellnessScore ? `${menta.wellnessScore}/100` : '80/100'}
              </div>
            </div>
            <p className="overview-banner-body">
              {menta?.mentaSummary ||
                'Menta synthesizes mood, energy, physical activity, and stress resilience into actionable daily guidance.'}
            </p>
          </div>
          <Link className="overview-banner-link" to="/app/wellness">
            Open Menta multi-pillar analysis <span>→</span>
          </Link>
        </div>
      </div>

      {/* Two Column Layout: Tools + Recent Activity */}
      <div className="dashboard-columns">
        <div>
          <div className="section-title">
            <h2>Your tools</h2>
            <span>Private by design</span>
          </div>
          <div className="dashboard-feature-grid">
            <FeatureCard
              icon="🍎"
              title="Food scanner"
              body="Check fresh produce, meal nutrition, and packaged foods with Nutri-Grade AI."
              to="/app/food"
              action="Scan food"
            />
            <FeatureCard
              icon="💬"
              title="Health chat"
              body="Ask for general health information with red-flag and escalation awareness."
              to="/app/chat"
              action="Ask health AI"
            />
            <FeatureCard
              icon="🧠"
              title="Mental wellness"
              body="Track SleepLM sleep summaries and Menta mood, energy, activity & stress trends."
              to="/app/wellness"
              action="Check in"
            />
          </div>
        </div>

        <div className="side-panel">
          <div className="section-title">
            <h2>Recent scan</h2>
            <Link to="/app/history">View all</Link>
          </div>
          {food[0] ? (
            <div className="recent-item">
              <span className="recent-emoji">🍎</span>
              <div>
                <b>{food[0].foodName}</b>
                <small>{food[0].condition}</small>
              </div>
              <strong>{food[0].freshnessScore}%</strong>
            </div>
          ) : (
            <div className="empty-state">Your analyzed food will appear here.</div>
          )}

          <div className="observation">
            <span>✦</span>
            <div>
              <b>Wellness trend observation</b>
              <p>
                {wellness?.analysis?.analysis ||
                  'Complete a check-in to receive a personal, non-diagnostic trend observation.'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <p className="medical-note">
        AI-generated information is not medical diagnosis or treatment. Seek professional care for concerning symptoms.
      </p>
    </section>
  );
}

function Metric({ label, value, icon }) {
  return (
    <div className="metric-card">
      <span>{icon}</span>
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}
