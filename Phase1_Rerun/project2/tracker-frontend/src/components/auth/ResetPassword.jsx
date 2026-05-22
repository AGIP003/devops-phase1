import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api from "../../services/api";

function ResetPassword() {
    const [searchParams] = useSearchParams();
    const token = searchParams.get("token") || "";
    const [formData, setFormData] = useState({
        password: "",
        confirmPassword: "",
    });
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    function handleChange(e) {
        const { name, value } = e.target;
        setFormData((prevFormData) => ({
            ...prevFormData,
            [name]: value,
        }));
    }

    function validateForm() {
        if (!token) {
            return "Reset token is missing";
        }

        if (!formData.password || !formData.confirmPassword) {
            return "Password and confirmation are required";
        }

        if (formData.password.length < 8) {
            return "Password must be at least 8 characters";
        }

        if (!/[A-Z]/.test(formData.password)) {
            return "Password must include an uppercase letter";
        }

        if (!/[a-z]/.test(formData.password)) {
            return "Password must include a lowercase letter";
        }

        if (!/\d/.test(formData.password)) {
            return "Password must include a number";
        }

        if (formData.password !== formData.confirmPassword) {
            return "Passwords do not match";
        }

        return "";
    }

    async function handleSubmit(e) {
        e.preventDefault();

        const error = validateForm();
        if (error) {
            setErrorMessage(error);
            setSuccessMessage("");
            return;
        }

        setLoading(true);
        setErrorMessage("");
        setSuccessMessage("");

        try {
            const response = await api.post("/auth/password-reset-verify", {
                token,
                new_password: formData.password,
            });
            setSuccessMessage(response.data?.message || "Password reset successfully");
            setFormData({
                password: "",
                confirmPassword: "",
            });
        } catch (err) {
            setErrorMessage(err.message || "Unable to reset password");
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
                    <h2>Reset password</h2>
                    <p>Choose a new password for your account.</p>
                </div>

                <div className="form-field">
                    <label htmlFor="reset-password">New password</label>
                    <input
                        id="reset-password"
                        type="password"
                        name="password"
                        placeholder="Enter new password"
                        value={formData.password}
                        onChange={handleChange}
                        disabled={loading || !token || Boolean(successMessage)}
                    />
                </div>

                <div className="form-field">
                    <label htmlFor="reset-confirm-password">Confirm password</label>
                    <input
                        id="reset-confirm-password"
                        type="password"
                        name="confirmPassword"
                        placeholder="Confirm new password"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        disabled={loading || !token || Boolean(successMessage)}
                    />
                </div>

                {!token && <div className="auth-message auth-message-error">Reset token is missing</div>}
                {errorMessage && <div className="auth-message auth-message-error">{errorMessage}</div>}
                {successMessage && <div className="auth-message auth-message-success">{successMessage}</div>}

                <button className="auth-submit" type="submit" disabled={loading || !token || Boolean(successMessage)}>
                    {loading ? "Resetting..." : "Reset password"}
                </button>

                <p className="auth-switch">
                    <Link to="/">Back to sign in</Link>
                </p>
            </form>
        </div>
    );
}

export default ResetPassword;
