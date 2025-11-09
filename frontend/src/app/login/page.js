"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await axios.post("/api/login/", form);
      const data = res.data;

      if (data.access) localStorage.setItem("access", data.access);
      if (data.refresh) localStorage.setItem("refresh", data.refresh);
      if (data.user) localStorage.setItem("user", JSON.stringify(data.user));

      setLoading(false);
      router.push("/dashboard");
    } catch (err) {
      if (err.response && err.response.data) setError(err.response.data);
      else setError({ detail: "Network error" });
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="w-full max-w-md bg-white p-6 rounded shadow">
        <h2 className="text-2xl font-semibold mb-4">Sign in</h2>

        {error && (
          <div className="mb-4 text-sm text-red-700">
            {error.detail && <div>{error.detail}</div>}
            {error.username && <div>{error.username}</div>}
            {error.password && <div>{error.password}</div>}
          </div>
        )}

        <div className="grid gap-3">
          <input name="username" placeholder="Username" value={form.username} onChange={handleChange} className="border rounded px-3 py-2" />
          <input name="password" type="password" placeholder="Password" value={form.password} onChange={handleChange} className="border rounded px-3 py-2" />

          <button type="submit" disabled={loading} className="mt-2 w-full bg-green-600 text-white py-2 rounded">
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </div>
      </form>
    </div>
  );
}
