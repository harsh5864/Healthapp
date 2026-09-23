import { Link } from 'react-router-dom';
import SiteHeader from '../components/SiteHeader';

export default function AboutPage() {
  return <main className="simple-page"><div className="landing-shell"><SiteHeader /><article className="prose-card"><p className="eyebrow">About the project</p><h1>Built to make everyday health decisions feel more informed.</h1><p>AI Health Companion is a BTech/hackathon full-stack project combining computer vision, conversational AI and trend analytics in one safety-first experience.</p><p>The architecture keeps the React client, Spring Boot business API, MySQL persistence and replaceable FastAPI AI adapters separate. That makes the demo easy to run today and ready for better models, wearables and clinician-facing workflows later.</p><p><strong>Our promise:</strong> be useful, be transparent about uncertainty and make professional care easier to seek—not easier to avoid.</p><Link className="button button--primary" to="/register">Get started</Link></article></div></main>;
}
