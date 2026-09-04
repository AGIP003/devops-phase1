import { useState } from "react";
import { Link } from "react-router-dom";
import { HandCoins } from "lucide-react";
import api from "../../services/api";

function ForgotPassword() {
    const passwordResetEnabled = (
        import.meta.env.VITE_PASSWORD_RESET_ENABLED === "true"
    );
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    async function handleSubmit(e) {
        e.preventDefault();

        if (!passwordResetEnabled) {
            return;
        }

        if (!email.trim()) {
            setErrorMessage("Email is required");
            setSuccessMessage("");
            return;
        }

        setLoading(true);
        setErrorMessage("");
        setSuccessMessage("");

        try {
            const response = await api.post("/auth/password_reset_request", {
                email: email.trim().toLowerCase(),
            });
            setSuccessMessage(response.data?.message || "A reset link has been sent");
        } catch (err) {
            setErrorMessage(err.message || "Unable to send reset link");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="auth-page">
            <form className="auth-form" onSubmit={handleSubmit}>
                <div className="auth-brand">
                    <div className="brand-mark" aria-hidden="true">
                        <HandCoins size={22} strokeWidth={2.2} />
                    </div>
                    <div>
                        <strong>Finance</strong>
                        <span>Tracker</span>
                    </div>
                </div>

                <div className="auth-heading">
                    <h2>Forgot password</h2>
                    <p>
                        {passwordResetEnabled
                            ? "Enter your email and we will send you a reset link."
                            : "Password recovery is temporarily paused while we improve email delivery."}
                    </p>
                </div>

                {!passwordResetEnabled && (
                    <div className="auth-feature-notice" role="status">
                        <strong>Reset links are unavailable right now</strong>
                        <span>
                            You can still sign in with your current password or
                            a Google account you previously linked.
                        </span>
                    </div>
                )}

                <div className={!passwordResetEnabled ? "auth-disabled-section" : undefined}>
                    <div className="form-field">
                        <label htmlFor="forgot-email">Email</label>
                        <input
                            id="forgot-email"
                            type="email"
                            name="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            disabled={!passwordResetEnabled || loading}
                        />
                    </div>

                    <button
                        className="auth-submit"
                        type="submit"
                        disabled={!passwordResetEnabled || loading}
                    >
                        {loading ? "Sending..." : "Send reset link"}
                    </button>
                </div>

                {errorMessage && <div className="auth-message auth-message-error">{errorMessage}</div>}
                {successMessage && <div className="auth-message auth-message-success">{successMessage}</div>}

                <p className="auth-switch">
                    Remembered your password? <Link to="/">Sign in</Link>
                </p>
            </form>
        </div>
    );
}

export default ForgotPassword;
