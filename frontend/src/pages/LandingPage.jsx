import { Link } from 'react-router-dom';
import ApiStatusBadge from '../components/ApiStatusBadge';
import SiteHeader from '../components/SiteHeader';

const features = [
  {
    icon: '🍎',
    title: 'Food Freshness Scanner',
    body: 'Upload a fruit or vegetable photo for AI-assisted visible-condition observations and freshness guidance.',
    phase: 'Available now · mock AI mode',
  },
  {
    icon: '💬',
    title: 'Smart Health Chat',
    body: 'Discuss everyday health questions and receive general, safety-conscious informational guidance.',
    phase: 'Available now · safety-aware chat',
  },
  {
    icon: '🧠',
    title: 'Mental Wellness',
    body: 'Track mood, stress, energy and sleep to understand personal patterns over time—without diagnosis.',
    phase: 'Available now · personal trends',
  },
];

export default function LandingPage() {
  return (
    <main>
      <div className="landing-shell">
        <SiteHeader />
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero__content">
            <p className="eyebrow"><span aria-hidden="true">✦</span> Everyday wellness, thoughtfully supported</p>
            <h1 id="hero-title">Your health questions deserve a calmer, clearer starting point.</h1>
            <p className="hero__summary">
              AI Health Companion brings food freshness checks, general health information and personal wellness trends
              into one private, human-centred space.
            </p>
            <div className="hero__actions">
              <a className="button button--primary" href="#features">Explore features <span aria-hidden="true">→</span></a>
              <Link className="button button--secondary" to="/safety">Our safety promise</Link>
            </div>
            <div className="hero__meta">
              <ApiStatusBadge />
              <span>Built for informed next steps, never diagnosis.</span>
            </div>
          </div>
          <div className="hero__visual" aria-label="Wellness overview illustration">
            <div className="orb orb--one" />
            <div className="orb orb--two" />
            <div className="wellness-card">
              <div className="wellness-card__top"><span>Today&apos;s wellbeing</span><span className="pulse">●</span></div>
              <div className="wellness-card__score">7.4 <small>/ 10</small></div>
              <p>Steady, with space to check in.</p>
              <div className="sparkline" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /></div>
            </div>
            <div className="float-card float-card--food"><span>🍎</span><div><b>Food scan</b><small>Visible checks only</small></div></div>
            <div className="float-card float-card--chat"><span>✦</span><div><b>Health guidance</b><small>Safety-first context</small></div></div>
          </div>
        </section>
      </div>

      <section className="feature-section" id="features" aria-labelledby="features-title">
        <div className="section-heading">
          <p className="eyebrow">One supportive home</p>
          <h2 id="features-title">Small everyday decisions, brought together.</h2>
          <p>Each tool has clear limits, plain-language explanations and a pathway to professional support when needed.</p>
        </div>
        <div className="feature-grid">
          {features.map((feature) => (
            <article className="feature-card" key={feature.title}>
              <span className="feature-card__icon" aria-hidden="true">{feature.icon}</span>
              <h3>{feature.title}</h3>
              <p>{feature.body}</p>
              <span className="feature-card__phase">{feature.phase}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="safety-banner" aria-labelledby="safety-title">
        <div><p className="eyebrow">Safety is a feature</p><h2 id="safety-title">AI can inform your next question. It cannot replace care.</h2></div>
        <Link to="/safety">Read safety &amp; privacy <span aria-hidden="true">→</span></Link>
      </section>
    </main>
  );
}
