import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";

function ForgotPassword() {
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    async function handleSubmit(e) {
        e.preventDefault();

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
                    <div className="brand-mark">F</div>
                    <div>
                        <strong>Finance</strong>
                        <span>Tracker</span>
                    </div>
                </div>

                <div className="auth-heading">
                    <h2>Forgot password</h2>
                    <p>Enter your email and we'll send you a reset link.</p>
                </div>

                <div className="form-field">
                    <label htmlFor="forgot-email">Email</label>
                    <input
                        id="forgot-email"
                        type="email"
                        name="email"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        disabled={loading}
                    />
                </div>

                {errorMessage && <div className="auth-message auth-message-error">{errorMessage}</div>}
                {successMessage && <div className="auth-message auth-message-success">{successMessage}</div>}

                <button className="auth-submit" type="submit" disabled={loading}>
                    {loading ? "Sending..." : "Send reset link"}
                </button>

                <p className="auth-switch">
                    Remembered your password? <Link to="/">Sign in</Link>
                </p>
            </form>
        </div>
    );
}

export default ForgotPassword;
