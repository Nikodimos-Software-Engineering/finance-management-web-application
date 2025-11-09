"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    username: "",
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    password2: "",
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState(null);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors(null);

    try {
      const res = await axios.post("/api/register", form);
      const data = res.data;

      if (data.access) localStorage.setItem("access", data.access);
      if (data.refresh) localStorage.setItem("refresh", data.refresh);
      if (data.user) localStorage.setItem("user", JSON.stringify(data.user));

      setLoading(false);
      router.push("/dashboard");
    } catch (err) {
      if (err.response && err.response.data) setErrors(err.response.data);
      else setErrors({ detail: "Network error" });
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="w-full max-w-md bg-white p-6 rounded shadow">
        <h2 className="text-2xl font-semibold mb-4">Create an account</h2>

        {errors && (
          <div className="mb-4 text-sm text-red-700">
            {typeof errors === "string" && <div>{errors}</div>}
            {errors.detail && <div>{errors.detail}</div>}
            {errors.password && <div>{errors.password}</div>}
            {errors.username && <div>{errors.username}</div>}
            {errors.email && <div>{errors.email}</div>}
            {errors.non_field_errors && <div>{errors.non_field_errors}</div>}
            {Object.keys(errors || {}).length === 0 && <div>Registration failed</div>}
          </div>
        )}

        <div className="grid gap-3">
          <input name="username" placeholder="Username" value={form.username} onChange={handleChange} className="border rounded px-3 py-2" />
          <input name="first_name" placeholder="First name" value={form.first_name} onChange={handleChange} className="border rounded px-3 py-2" />
          <input name="last_name" placeholder="Last name" value={form.last_name} onChange={handleChange} className="border rounded px-3 py-2" />
          <input name="email" placeholder="Email" value={form.email} onChange={handleChange} className="border rounded px-3 py-2" />
          <input name="password" type="password" placeholder="Password" value={form.password} onChange={handleChange} className="border rounded px-3 py-2" />
          <input name="password2" type="password" placeholder="Confirm Password" value={form.password2} onChange={handleChange} className="border rounded px-3 py-2" />

          <button type="submit" disabled={loading} className="mt-2 w-full bg-blue-600 text-white py-2 rounded">
            {loading ? "Registering..." : "Register"}
          </button>
        </div>
      </form>
    </div>
  );
}
