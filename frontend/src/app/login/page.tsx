"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { requestMagicLink } from "@/api/auth"
import { PATHS } from "@/constants/fe_config";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(false);
    setError("");
    setLoading(true);

    try {
      const res = await requestMagicLink(email);

      if (res.ok) {
        setSubmitted(true);
        router.push(PATHS.WAITING);
      } else {
        const data = await res.json();
        setError(data?.detail || "Login failed");
      }
    } catch (err) {
      setError("Unexpected error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen text-white flex items-center justify-center px-4">
      <form
        onSubmit={handleLogin}
        className="w-full max-w-md space-y-5 p-8 rounded-lg shadow-md border border-gray-800"
      >
        <h1 className="text-3xl font-bold text-center">Sign in</h1>

        <div>
          <label htmlFor="email" className="block mb-2 text-sm font-medium">
            Email address
          </label>
          <input
            id="email"
            type="email"
            required
            placeholder="you@example.com"
            className="w-full p-3 bg-gray-800 text-white border border-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-[#09BDE1]"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !email}
          className="w-full bg-[#09BDE1] hover:bg-[#08A4C4] text-white font-semibold py-2 px-4 rounded transition-colors disabled:opacity-50"
        >
          {loading ? "Signing In" : "Sign In"}
        </button>

        {submitted && (
          <p className="text-green-500 text-sm text-center">
            ✅ Magic link sent! Check your inbox.
          </p>
        )}

        {error && (
          <p className="text-red-500 text-sm text-center">⚠️ {error}</p>
        )}
      </form>
    </div>
  );
}