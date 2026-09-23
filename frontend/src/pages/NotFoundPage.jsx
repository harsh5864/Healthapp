import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return <main className="not-found"><p className="eyebrow">404</p><h1>That page is not here.</h1><Link className="button button--primary" to="/">Return home</Link></main>;
}
