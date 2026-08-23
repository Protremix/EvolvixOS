import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const Verify = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState(location.state?.email || "");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resent, setResent] = useState(false);
  const [infoMsg] = useState(location.state?.message || "");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/auth/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "Verification failed");
      localStorage.setItem("evolvixos_token", data.token);
      localStorage.setItem("evolvixos_user", JSON.stringify(data.user || { email }));
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError("");
    try {
      const res = await fetch("/auth/resend-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "Could not resend code");
      setResent(true);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0b]">
      <div className="w-full max-w-md p-8 bg-[#111113] rounded-xl border border-[#1f1f23]">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">Verify Your Email</h1>
          <p className="text-gray-500 mt-2 text-sm">
            Enter the 6-digit code sent to your Telegram, or contact an admin for your code.
          </p>
        </div>
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 text-red-400 rounded-lg text-sm border border-red-500/20">
            {error}
          </div>
        )}
        {infoMsg && (
          <div className="mb-4 p-3 bg-teal-500/10 text-teal-400 rounded-lg text-sm border border-teal-500/20">
            {infoMsg}
          </div>
        )}
        {resent && (
          <div className="mb-4 p-3 bg-teal-500/10 text-teal-400 rounded-lg text-sm border border-teal-500/20">
            A new code has been generated and sent to your email.
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2.5 bg-[#0a0a0b] border border-[#1f1f23] rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-teal-400/50 focus:ring-1 focus:ring-teal-400/20 transition-all"
              placeholder="you@evolvixos.com"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Verification Code</label>
            <input
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              required
              maxLength={6}
              className="w-full px-4 py-2.5 bg-[#0a0a0b] border border-[#1f1f23] rounded-lg text-white placeholder-gray-600 tracking-widest text-center text-lg focus:outline-none focus:border-teal-400/50 focus:ring-1 focus:ring-teal-400/20 transition-all"
              placeholder="000000"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-teal-400 text-[#0a0a0b] rounded-lg font-medium hover:bg-teal-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Verifying..." : "Verify"}
          </button>
        </form>
        <p className="text-center text-gray-500 mt-4 text-sm">
          Didn't get a code?{" "}
          <button onClick={handleResend} className="text-teal-400 hover:underline">Resend</button>
        </p>
      </div>
    </div>
  );
};

export default Verify;
