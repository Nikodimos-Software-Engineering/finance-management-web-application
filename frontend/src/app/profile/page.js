"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const raw = localStorage.getItem("user");
      if (!raw || !localStorage.getItem("access")) {
        router.replace("/");
        return;
      }
      try {
        setUser(JSON.parse(raw));
      } catch {
        router.replace("/");
      }
    }
  }, [router]);

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="bg-white rounded-lg shadow w-full max-w-md p-6">
        <h1 className="text-2xl font-semibold mb-6">Profile</h1>
        <div className="space-y-3">
          <div>
            <span className="text-sm text-gray-500">Username</span>
            <p className="font-medium">{user.username}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Name</span>
            <p className="font-medium">{[user.first_name, user.last_name].filter(Boolean).join(" ") || "—"}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Email</span>
            <p className="font-medium">{user.email || "—"}</p>
          </div>
        </div>
        <button
          onClick={() => router.push("/dashboard")}
          className="mt-6 px-4 py-2 bg-blue-600 text-white rounded"
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}
