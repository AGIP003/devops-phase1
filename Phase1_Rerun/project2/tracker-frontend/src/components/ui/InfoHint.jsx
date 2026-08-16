import { useEffect, useId, useRef, useState } from "react";
import { Info } from "lucide-react";


function InfoHint({ label, text }) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef(null);
  const tooltipId = `info-hint-${useId().replaceAll(":", "")}`;

  useEffect(() => {
    if (!open) return undefined;
    function closeOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    function closeWithEscape(event) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("keydown", closeWithEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("keydown", closeWithEscape);
    };
  }, [open]);

  return (
    <span className={`info-hint ${open ? "open" : ""}`} ref={wrapperRef}>
      <button
        type="button"
        className="info-hint-trigger"
        aria-label={`About ${label}`}
        aria-describedby={open ? tooltipId : undefined}
        aria-expanded={open}
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          setOpen((current) => !current);
        }}
      >
        <Info size={13} aria-hidden="true" />
      </button>
      <span className="info-hint-popover" id={tooltipId} role="tooltip">
        {text}
      </span>
    </span>
  );
}

export default InfoHint;
