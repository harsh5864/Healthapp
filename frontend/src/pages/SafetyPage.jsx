import { Link } from 'react-router-dom';
import SiteHeader from '../components/SiteHeader';

export default function SafetyPage() {
  return (
    <main className="simple-page">
      <div className="landing-shell">
        <SiteHeader />
        <article className="prose-card">
          <p className="eyebrow">Safety &amp; privacy</p>
          <h1>Designed to support—not diagnose.</h1>
          <p>AI Health Companion will provide general, informational guidance. It will not diagnose conditions, prescribe treatment or replace a qualified healthcare professional.</p>
          <p><strong>For urgent or severe symptoms, seek emergency care immediately.</strong> Food image analysis can assess only visible characteristics; it cannot detect bacteria, toxins, internal spoilage or every food-safety risk.</p>
          <p>Wellness trends and journal-language patterns are personal reflections, not mental-health diagnoses. If changes persist or affect daily life, consider talking with someone you trust or a qualified professional.</p>
          <Link className="button button--primary" to="/">Back home</Link>
        </article>
      </div>
    </main>
  );
}
