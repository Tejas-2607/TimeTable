// src/components/ResetPassword.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lock, ArrowLeft, CheckCircle, Mail } from "lucide-react";
import { resetPassword } from "../services/authService";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";

export default function ResetPassword() {
  const { user } = useAuth();
  const [step, setStep] = useState(user ? "authenticated" : "email"); // "email", "reset", "authenticated"
  const [email, setEmail] = useState("");
  const [formData, setFormData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  // For unauthenticated users - verify email exists
  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (!email) {
      setError("Email is required");
      setLoading(false);
      return;
    }

    try {
      // In a real scenario, you'd call an API to verify the email exists
      // For now, we'll proceed to the reset form
      setStep("reset");
    } catch (err) {
      setError("Failed to verify email");
    } finally {
      setLoading(false);
    }
  };

  // For unauthenticated users - reset password with email
  const handleForgotPasswordSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    if (!formData.current_password || !formData.new_password || !formData.confirm_password) {
      setError("All password fields are required");
      setLoading(false);
      return;
    }

    if (formData.new_password !== formData.confirm_password) {
      setError("New password and confirm password do not match");
      setLoading(false);
      return;
    }

    if (formData.new_password.length < 6) {
      setError("Password must be at least 6 characters long");
      setLoading(false);
      return;
    }

    try {
      // Call forgot password endpoint
      const response = await api.post("/auth/forgot-password", {
        email: email,
        current_password: formData.current_password,
        new_password: formData.new_password,
        confirm_password: formData.confirm_password,
      });

      setSuccess("Password reset successfully! Redirecting to login...");
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err) {
      const serverError = err.response?.data?.error;
      const status = err.response?.status;

      if (status === 401) {
        setError(
          serverError || "Current password is incorrect. Please try again.",
        );
      } else if (status === 404) {
        setError(serverError || "Faculty not found with this email.");
      } else if (status >= 500) {
        setError("Server error. Please wait a moment or contact support.");
      } else {
        setError(serverError || "Failed to reset password. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  // For authenticated users - change password
  const handleAuthenticatedSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    if (
      !formData.current_password ||
      !formData.new_password ||
      !formData.confirm_password
    ) {
      setError("All fields are required");
      setLoading(false);
      return;
    }

    if (formData.new_password !== formData.confirm_password) {
      setError("New password and confirm password do not match");
      setLoading(false);
      return;
    }

    if (formData.new_password.length < 6) {
      setError("Password must be at least 6 characters long");
      setLoading(false);
      return;
    }

    try {
      const response = await resetPassword(formData);
      setSuccess("Password updated successfully!");
      setFormData({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err) {
      const serverError = err.response?.data?.error;
      const status = err.response?.status;

      if (status === 401) {
        setError(
          serverError || "Current password is incorrect. Please try again.",
        );
      } else if (status === 404) {
        setError("Faculty profile not found. Please log in again.");
      } else if (status >= 500) {
        setError("Server error. Please wait a moment or contact support.");
      } else {
        setError(
          serverError || "Failed to reset password. Please try again.",
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const PasswordInput = ({ label, name, value, showPasswordKey }) => {
    const show = showPassword[showPasswordKey];
    return (
      <div className="relative group">
        <label className="block text-white/70 text-sm font-medium mb-2">
          {label}
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-white/40 group-focus-within:text-blue-400 transition-colors">
            <Lock size={18} />
          </div>
          <input
            type={show ? "text" : "password"}
            name={name}
            placeholder={label}
            required
            value={value}
            onChange={handleInputChange}
            className="w-full bg-white/5 border border-white/10 text-white pl-11 pr-12 py-3 rounded-xl focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all placeholder:text-white/20"
          />
          <button
            type="button"
            onClick={() =>
              setShowPassword({
                ...showPassword,
                [showPasswordKey]: !show,
              })
            }
            className="absolute inset-y-0 right-0 pr-4 flex items-center text-white/40 hover:text-white/60 transition-colors"
          >
            {show ? "Hide" : "Show"}
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-indigo-900 to-slate-900 p-4 font-sans relative overflow-hidden">
      {/* Background blobs for aesthetics */}
      <div className="absolute top-0 -left-20 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl" />
      <div className="absolute -bottom-20 -right-20 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl" />

      <div className="w-full max-w-md relative z-10">
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl shadow-2xl overflow-hidden">
          <div className="p-8">
            {/* Header */}
            <button
              onClick={() => navigate("/login")}
              className="flex items-center gap-2 text-blue-300 hover:text-blue-200 transition-colors mb-6 font-medium text-sm"
            >
              <ArrowLeft size={18} />
              Back to Login
            </button>

            {step === "email" ? (
              <>
                <div className="text-center mb-8">
                  <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-2xl shadow-lg shadow-blue-500/30 mb-4">
                    <Mail className="text-white" size={28} />
                  </div>
                  <h1 className="text-2xl font-bold text-white mb-2">
                    Reset Password
                  </h1>
                  <p className="text-blue-200/70 text-sm">
                    Enter your email to reset your password
                  </p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-200 text-sm flex items-center gap-3">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                    {error}
                  </div>
                )}

                <form onSubmit={handleEmailSubmit} className="space-y-5">
                  <div className="relative group">
                    <label className="block text-white/70 text-sm font-medium mb-2">
                      Email Address
                    </label>
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-white/40 group-focus-within:text-blue-400 transition-colors mt-8">
                      <Mail size={18} />
                    </div>
                    <input
                      type="email"
                      placeholder="Enter your registered email"
                      required
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        setError("");
                      }}
                      className="w-full bg-white/5 border border-white/10 text-white pl-11 pr-4 py-3 rounded-xl focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all placeholder:text-white/20"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-blue-500/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2 group disabled:opacity-50 mt-6"
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>Continue</span>
                        <ArrowLeft size={18} className="rotate-180" />
                      </>
                    )}
                  </button>
                </form>
              </>
            ) : step === "reset" ? (
              <>
                <div className="text-center mb-8">
                  <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-2xl shadow-lg shadow-blue-500/30 mb-4">
                    <Lock className="text-white" size={28} />
                  </div>
                  <h1 className="text-2xl font-bold text-white mb-2">
                    Set New Password
                  </h1>
                  <p className="text-blue-200/70 text-sm">
                    Create a strong new password for {email}
                  </p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-200 text-sm flex items-center gap-3">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                    {error}
                  </div>
                )}

                {success && (
                  <div className="mb-6 p-4 bg-green-500/20 border border-green-500/30 rounded-xl text-green-200 text-sm flex items-center gap-3">
                    <CheckCircle size={18} />
                    {success}
                  </div>
                )}

                <form onSubmit={handleForgotPasswordSubmit} className="space-y-5">
                  <PasswordInput
                    label="Current Password"
                    name="current_password"
                    value={formData.current_password}
                    showPasswordKey="current"
                  />

                  <PasswordInput
                    label="New Password"
                    name="new_password"
                    value={formData.new_password}
                    showPasswordKey="new"
                  />

                  <PasswordInput
                    label="Confirm New Password"
                    name="confirm_password"
                    value={formData.confirm_password}
                    showPasswordKey="confirm"
                  />

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-blue-500/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2 group disabled:opacity-50 mt-6"
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>Reset Password</span>
                        <CheckCircle size={18} className="group-hover:scale-110 transition-transform" />
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setStep("email");
                      setEmail("");
                      setFormData({
                        current_password: "",
                        new_password: "",
                        confirm_password: "",
                      });
                      setError("");
                    }}
                    className="w-full text-blue-300 hover:text-blue-200 transition-colors text-sm font-medium py-2"
                  >
                    Use different email
                  </button>
                </form>

                <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                  <p className="text-blue-200/70 text-xs font-medium mb-2">
                    Password Requirements:
                  </p>
                  <ul className="text-blue-200/60 text-xs space-y-1">
                    <li>• At least 6 characters long</li>
                    <li>• Must match in the confirm field</li>
                  </ul>
                </div>
              </>
            ) : (
              <>
                <div className="text-center mb-8">
                  <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-2xl shadow-lg shadow-blue-500/30 mb-4">
                    <Lock className="text-white" size={28} />
                  </div>
                  <h1 className="text-2xl font-bold text-white mb-2">
                    Change Password
                  </h1>
                  <p className="text-blue-200/70 text-sm">
                    Update your password to keep your account secure
                  </p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl text-red-200 text-sm flex items-center gap-3 animate-head-shake">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                    {error}
                  </div>
                )}

                {success && (
                  <div className="mb-6 p-4 bg-green-500/20 border border-green-500/30 rounded-xl text-green-200 text-sm flex items-center gap-3">
                    <CheckCircle size={18} />
                    {success}
                  </div>
                )}

                <form onSubmit={handleAuthenticatedSubmit} className="space-y-5">
                  <PasswordInput
                    label="Current Password"
                    name="current_password"
                    value={formData.current_password}
                    showPasswordKey="current"
                  />

                  <PasswordInput
                    label="New Password"
                    name="new_password"
                    value={formData.new_password}
                    showPasswordKey="new"
                  />

                  <PasswordInput
                    label="Confirm New Password"
                    name="confirm_password"
                    value={formData.confirm_password}
                    showPasswordKey="confirm"
                  />

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-blue-500/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2 group disabled:opacity-50 mt-6"
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>Update Password</span>
                        <CheckCircle size={18} className="group-hover:scale-110 transition-transform" />
                      </>
                    )}
                  </button>
                </form>

                <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                  <p className="text-blue-200/70 text-xs font-medium mb-2">
                    Password Requirements:
                  </p>
                  <ul className="text-blue-200/60 text-xs space-y-1">
                    <li>• At least 6 characters long</li>
                    <li>• Must match in the confirm field</li>
                  </ul>
                </div>
              </>
            )}
          </div>
        </div>

        <p className="mt-8 text-center text-white/20 text-xs">
          &copy; 2026 Schedulo Timetable System. All rights reserved.
        </p>
      </div>
    </div>
  );
}
