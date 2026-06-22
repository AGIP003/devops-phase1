/* eslint-disable react/prop-types */
import { Check, Copy, RefreshCw, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import toast from "react-hot-toast";

import api from "../../services/api";


export function TelegramIcon({ size = 18, ...props }) {
    return (
        <svg
            viewBox="0 0 24 24"
            width={size}
            height={size}
            fill="none"
            aria-hidden="true"
            {...props}
        >
            <path
                fill="currentColor"
                d="M21.7 3.35a1.6 1.6 0 0 0-1.66-.2L2.9 9.82c-1.22.47-1.2 1.18-.22 1.48l4.4 1.37 1.7 5.2c.2.57.1.8.68.8.45 0 .65-.2.9-.45l2.13-2.07 4.43 3.27c.82.45 1.4.22 1.61-.76l2.92-13.77c.3-1.2-.46-1.75-1.24-1.4L7.8 11.1c-.85.34-.84.82-.15 1.03l3.18.99 7.38-4.66c.35-.22.67-.1.4.14l-6.08 5.49-.24 3.5c.35 0 .5-.16.7-.35l1.68-1.63 3.5 2.58 2.03-12.77c.15-.91-.22-1.34-.5-2.07Z"
            />
        </svg>
    );
}


function TelegramLinkPanel({ open, onClose, onStatusChange }) {
    const [status, setStatus] = useState({ linked: false, telegram_id: null });
    const [linkCode, setLinkCode] = useState("");
    const [expiresAt, setExpiresAt] = useState("");
    const [loadingStatus, setLoadingStatus] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [setupError, setSetupError] = useState("");

    const fetchStatus = useCallback(async () => {
        setLoadingStatus(true);
        setSetupError("");
        try {
            const response = await api.get("/telegram/status");
            setStatus(response.data);
            onStatusChange(Boolean(response.data?.linked));
        } catch (error) {
            setStatus({ linked: false, telegram_id: null });
            onStatusChange(false);
            setSetupError(error.message);
        } finally {
            setLoadingStatus(false);
        }
    }, [onStatusChange]);

    useEffect(() => {
        if (!open) return undefined;

        fetchStatus();
        function closeOnEscape(event) {
            if (event.key === "Escape") onClose();
        }
        window.addEventListener("keydown", closeOnEscape);
        return () => window.removeEventListener("keydown", closeOnEscape);
    }, [fetchStatus, onClose, open]);

    async function generateCode() {
        setGenerating(true);
        setSetupError("");
        try {
            const response = await api.post("/telegram/link-token");
            setLinkCode(response.data.token);
            setExpiresAt(response.data.expires_at);
            toast.success("Telegram link code generated");
        } catch (error) {
            setSetupError(error.message);
        } finally {
            setGenerating(false);
        }
    }

    async function copyCommand() {
        const command = `/link ${linkCode}`;
        try {
            await navigator.clipboard.writeText(command);
            toast.success("Link command copied");
        } catch {
            toast.error("Could not copy the command");
        }
    }

    if (!open) return null;

    const expiryLabel = expiresAt
        ? new Intl.DateTimeFormat("en-KE", {
            hour: "2-digit",
            minute: "2-digit",
        }).format(new Date(expiresAt))
        : "";

    return (
        <div className="telegram-panel-backdrop" onMouseDown={onClose}>
            <section
                className="telegram-panel"
                role="dialog"
                aria-modal="true"
                aria-labelledby="telegram-panel-title"
                onMouseDown={(event) => event.stopPropagation()}
            >
                <div className="telegram-panel-header">
                    <div className="telegram-panel-heading">
                        <span className="telegram-panel-logo">
                            <TelegramIcon size={22} />
                        </span>
                        <div>
                            <p>Integration</p>
                            <h2 id="telegram-panel-title">Connect Telegram</h2>
                        </div>
                    </div>
                    <button
                        type="button"
                        className="telegram-panel-close"
                        aria-label="Close Telegram panel"
                        onClick={onClose}
                    >
                        <X size={18} />
                    </button>
                </div>

                <div className={`telegram-status ${status.linked ? "is-linked" : ""}`}>
                    <span className="telegram-status-icon">
                        {status.linked ? <Check size={16} /> : <TelegramIcon size={16} />}
                    </span>
                    <div>
                        <strong>
                            {loadingStatus
                                ? "Checking connection..."
                                : status.linked
                                    ? "Telegram connected"
                                    : "Not connected"}
                        </strong>
                        <p>
                            {status.linked
                                ? "Your Telegram account can securely access Finance Tracker."
                                : "Generate a private, short-lived code to connect your account."}
                        </p>
                    </div>
                </div>

                {setupError && (
                    <div className="telegram-setup-error" role="alert">
                        {setupError}
                    </div>
                )}

                {!status.linked && (
                    <>
                        <ol className="telegram-steps">
                            <li>Generate a one-time code below.</li>
                            <li>Open the Finance Tracker bot in Telegram.</li>
                            <li>Send the generated <code>/link</code> command.</li>
                        </ol>

                        {linkCode ? (
                            <div className="telegram-code-block">
                                <span>Send this command to the bot</span>
                                <code>/link {linkCode}</code>
                                <div className="telegram-code-actions">
                                    <small>Expires at {expiryLabel}</small>
                                    <div>
                                        <button type="button" onClick={fetchStatus}>
                                            <RefreshCw size={15} />
                                            Status
                                        </button>
                                        <button type="button" onClick={copyCommand}>
                                            <Copy size={15} />
                                            Copy
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <button
                                type="button"
                                className="telegram-generate-button"
                                disabled={generating || Boolean(setupError)}
                                onClick={generateCode}
                            >
                                {generating ? <RefreshCw className="spin" size={17} /> : <TelegramIcon size={17} />}
                                {generating ? "Generating..." : "Generate link code"}
                            </button>
                        )}
                    </>
                )}

                <p className="telegram-security-note">
                    Your password is never shared with Telegram. Codes expire after 10 minutes and work only once.
                </p>
            </section>
        </div>
    );
}

export default TelegramLinkPanel;
