import { PlusCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function EmptyState({ title, message, actionLabel, actionPath }) {
  const navigate = useNavigate();

  return (
    <div className="empty-state">
      <PlusCircle size={48} />
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-message">{message}</p>
      {actionLabel && actionPath && (
        <button className="btn-primary" onClick={() => navigate(actionPath)}>
          <PlusCircle size={16} />
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export default EmptyState;