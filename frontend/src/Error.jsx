export default function Error(message, onClose) {
  if (!message) return null;

  return (
    <div className="error-popup-overlay">
      <div className="error-popup">
        <div className="error-popup-header">
          <span>Error</span>
          <button className="error-close-btn" onClick={onClose}>
            &times;
          </button>
        </div>
        <div className="error-popup-body">{message}</div>
      </div>
    </div>
  );
}
