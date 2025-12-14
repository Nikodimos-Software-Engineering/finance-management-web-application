"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/utils/api";

function currency(n) {
  return `$${Number(n || 0).toFixed(2)}`;
}

function CircularRing({ pct, size = 72, stroke = 8 }) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.max(0, Math.min(100, pct)) / 100) * circumference;
  const color = pct < 60 ? "#10b981" : pct < 90 ? "#f59e0b" : "#ef4444";

  return (
    <svg width={size} height={size} className="block">
      <g transform={`translate(${size / 2}, ${size / 2})`}>
        <circle r={radius} fill="#fff" stroke="#f3f4f6" strokeWidth={stroke} />
        <circle
          r={radius}
          fill="transparent"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90)`}
        />
        <text x="0" y="4" textAnchor="middle" className="text-xs font-semibold" fill="#111">{`${Math.round(pct)}%`}</text>
      </g>
    </svg>
  );
}

function SummaryCard({ title, value, emoji }) {
  return (
    <div className="p-4 rounded-lg shadow-sm transform transition hover:-translate-y-1 bg-gradient-to-r from-white to-gray-50">
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">{title}</div>
        <div className="text-2xl">{emoji}</div>
      </div>
      <div className="mt-3 text-xl font-semibold">{value}</div>
    </div>
  );
}

export default function BudgetPage() {
  const [budgets, setBudgets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const itemsPerPage = 6;

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const [formCategory, setFormCategory] = useState("");
  const [formAmount, setFormAmount] = useState(0);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    load();
    fetchCategories();
  }, []);

  function getHeaders() {
    const headers = {};
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }
    return headers;
  }

  async function load() {
    setLoading(true);
    try {
      const data = await apiFetch("api/budgets/", {
        headers: getHeaders(),
      });
      setBudgets(data || []);
    } catch (err) {
      console.error(err);
      setBudgets([]);
    } finally {
      setLoading(false);
    }
  }

  async function fetchCategories() {
    try {
      const data = await apiFetch("api/categories/", {
        headers: getHeaders(),
      });
      const expense = (data || []).filter((c) => c.type === "expense");
      setCategories(expense);
    } catch (err) {
      setCategories([]);
    }
  }

  function computeSummary() {
    const totalBudgeted = budgets.reduce((s, b) => s + Number(b.allocated_amount || 0), 0);
    const totalRemaining = budgets.reduce((s, b) => s + Number(b.remaining_amount || 0), 0);
    const totalSpent = totalBudgeted - totalRemaining;
    const avgUsage = budgets.length ? (totalSpent / totalBudgeted) * 100 : 0;
    return { totalBudgeted, totalSpent, totalRemaining, avgUsage };
  }

  const { totalBudgeted, totalSpent, totalRemaining, avgUsage } = computeSummary();

  const totalPages = Math.max(1, Math.ceil(budgets.length / itemsPerPage));
  const paginated = budgets.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  function openCreate() {
    setEditing(null);
    setFormCategory(categories.length ? categories[0].id : "");
    setFormAmount(0);
    setModalOpen(true);
  }

  function openEdit(b) {
    setEditing(b);
    setFormCategory(b.category?.id || "");
    setFormAmount(Number(b.allocated_amount || 0));
    setModalOpen(true);
  }

  async function handleSave() {
    if (!formCategory) return alert("Select a category");
    if (!formAmount || Number(formAmount) <= 0) return alert("Enter a positive planned amount");
    setSaving(true);
    try {
      if (editing) {
        const payload = { category_id: formCategory, allocated_amount: formAmount };
        const data = await apiFetch(`api/budgets/${editing.id}/`, {
          method: "PUT",
          headers: getHeaders(),
          body: JSON.stringify(payload),
        });
        setBudgets((prev) => prev.map((p) => (p.id === data.id ? data : p)));
      } else {
        const payload = { category_id: formCategory, allocated_amount: formAmount };
        const data = await apiFetch("api/budgets/", {
          method: "POST",
          headers: getHeaders(),
          body: JSON.stringify(payload),
        });
        setBudgets((prev) => [data, ...(prev || [])]);
      }
      setModalOpen(false);
    } catch (err) {
      console.error(err);
      alert("Failed to save budget");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(b) {
    if (!confirm("Delete this budget?")) return;
    const prev = budgets;
    setBudgets(prev.filter((x) => x.id !== b.id));
    try {
      await apiFetch(`api/budgets/${b.id}/`, {
        method: "DELETE",
        headers: getHeaders(),
      });
    } catch (err) {
      console.error(err);
      setBudgets(prev);
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-6">Budgets</h1>

      {/* Summary zone */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-r from-indigo-50 to-white p-4 rounded-lg shadow-sm">
          <SummaryCard title="Total Budgeted" value={currency(totalBudgeted)} emoji="💰" />
        </div>
        <div className="bg-gradient-to-r from-rose-50 to-white p-4 rounded-lg shadow-sm">
          <SummaryCard title="Total Spent" value={currency(totalSpent)} emoji="📉" />
        </div>
        <div className="bg-gradient-to-r from-green-50 to-white p-4 rounded-lg shadow-sm">
          <SummaryCard title="Remaining" value={currency(totalRemaining)} emoji="🧾" />
        </div>
        <div className="bg-gradient-to-r from-yellow-50 to-white p-4 rounded-lg shadow-sm">
          <SummaryCard title="Average Usage" value={`${Math.round(avgUsage || 0)}%`} emoji="📊" />
        </div>
      </div>

      {/* Grid header with floating add button */}
      <div className="relative">
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {paginated.map((b) => {
            const allocated = Number(b.allocated_amount || 0);
            const remaining = Number(b.remaining_amount || 0);
            const spent = allocated - remaining;
            const pct = allocated ? (spent / allocated) * 100 : 0;
            return (
              <div key={b.id} className="bg-white rounded-lg p-4 shadow transition transform hover:-translate-y-1">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-sm text-gray-500">{b.category?.name || "Unknown"}</div>
                    <div className="text-lg font-semibold">{currency(allocated)}</div>
                    <div className="text-xs text-gray-400">Planned</div>
                  </div>
                  <div className="flex flex-col items-end">
                    <CircularRing pct={pct} />
                    <div className="text-sm mt-2">Spent {Math.round(pct)}%</div>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2 text-sm text-gray-600">
                  <div>
                    <div className="font-medium">{currency(spent)}</div>
                    <div className="text-xs">Spent</div>
                  </div>
                  <div>
                    <div className="font-medium">{currency(remaining)}</div>
                    <div className="text-xs">Remaining</div>
                  </div>
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openEdit(b)} className="px-2 py-1 bg-blue-600 text-white rounded text-xs">Edit</button>
                    <button onClick={() => handleDelete(b)} className="px-2 py-1 bg-red-600 text-white rounded text-xs">Delete</button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Floating add button */}
        <button
          onClick={openCreate}
          className="fixed right-8 top-36 bg-blue-600 text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg hover:scale-105 transition"
          aria-label="Add budget"
        >
          +
        </button>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-center gap-4 mt-6">
        <button onClick={() => setPage((p) => Math.max(1, p - 1))} className="px-3 py-1 border rounded disabled:opacity-50" disabled={page === 1}>
          Prev
        </button>
        <div className="text-sm">Page {page} of {totalPages}</div>
        <button onClick={() => setPage((p) => (p < totalPages ? p + 1 : p))} className="px-3 py-1 border rounded disabled:opacity-50" disabled={page >= totalPages}>
          Next
        </button>
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg w-full max-w-md p-6">
            <h3 className="text-lg font-semibold mb-3">{editing ? "Edit Budget" : "Create Budget"}</h3>
            <div className="grid grid-cols-1 gap-3">
              <label className="text-sm">Category</label>
              <select value={formCategory} onChange={(e) => setFormCategory(e.target.value)} className="w-full border rounded px-2 py-1">
                <option value="">Select category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>

              <label className="text-sm">Planned amount</label>
              <input type="number" step="0.01" value={formAmount} onChange={(e) => setFormAmount(e.target.value)} className="w-full border rounded px-2 py-1" />

              <div className="flex items-center gap-4">
                <div className="w-24">
                  <CircularRing pct={0} />
                </div>
                <div className="text-sm text-gray-500">Planned: {currency(formAmount)}</div>
              </div>

              <div className="flex justify-end gap-2 mt-3">
                <button onClick={() => { setModalOpen(false); setEditing(null); }} className="px-3 py-2 border rounded">Cancel</button>
                <button onClick={handleSave} className="px-3 py-2 bg-blue-600 text-white rounded" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}