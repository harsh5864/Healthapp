import { useEffect, useState } from 'react';
import { getApiStatus } from '../services/platformService';

export default function ApiStatusBadge() {
  const [connection, setConnection] = useState('connecting');

  useEffect(() => {
    let active = true;

    getApiStatus()
      .then((status) => {
        if (active) setConnection(status.aiMode === 'mock' ? 'mock' : 'online');
      })
      .catch(() => {
        if (active) setConnection('offline');
      });

    return () => {
      active = false;
    };
  }, []);

  const labels = {
    connecting: 'Connecting to secure API',
    online: 'Secure API connected',
    mock: 'Secure API connected · mock AI mode',
    offline: 'API unavailable locally',
  };

  return (
    <span className={`api-status api-status--${connection}`} aria-live="polite">
      <span aria-hidden="true" className="api-status__dot" />
      {labels[connection]}
    </span>
  );
}
