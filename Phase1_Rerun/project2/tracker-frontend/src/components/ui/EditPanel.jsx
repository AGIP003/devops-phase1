import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";


function EditPanel({
  children,
  error,
  eyebrow = "Edit record",
  onClose,
  onSubmit,
  saving = false,
  submitLabel = "Save changes",
  title,
}) {
  const titleId = useId();
  const closeButtonRef = useRef(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    function handleEscape(event) {
      if (event.key === "Escape" && !saving) onCloseRef.current();
    }

    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = previousOverflow;
    };
  }, [saving]);

  return (
    <div
      className="edit-panel-backdrop"
      onPointerDown={(event) => {
        event.stopPropagation();
        if (event.target === event.currentTarget && !saving) onClose();
      }}
    >
      <section
        aria-labelledby={titleId}
        aria-modal="true"
        className="edit-panel"
        role="dialog"
      >
        <form className="edit-panel-form" onSubmit={onSubmit}>
          <header className="edit-panel-header">
            <div>
              <span>{eyebrow}</span>
              <h2 id={titleId}>{title}</h2>
            </div>
            <button
              aria-label="Close edit form"
              className="debt-icon-button"
              disabled={saving}
              onClick={onClose}
              ref={closeButtonRef}
              type="button"
            >
              <X size={19} aria-hidden="true" />
            </button>
          </header>

          <div className="edit-panel-body">{children}</div>

          {error && <p className="debt-form-error" role="alert">{error}</p>}
          <footer className="edit-panel-actions">
            <button
              className="debt-secondary-button"
              disabled={saving}
              onClick={onClose}
              type="button"
            >
              Cancel
            </button>
            <button
              className="feature-primary-button"
              disabled={saving}
              type="submit"
            >
              {saving ? "Saving…" : submitLabel}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

export default EditPanel;
