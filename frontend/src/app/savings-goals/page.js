"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/utils/api";

function pctToColor(pct) {
  if (pct <= 33) return "bg-red-500";
  if (pct <= 66) return "bg-orange-400";
  return "bg-green-500";
}

function HorizontalProgress({ value }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)));
  const colorClass = pctToColor(pct);
  return (
    <div className="w-full h-3 bg-gray-200 rounded overflow-hidden">
      <div className={`${colorClass} h-full`} style={{ width: `${pct}%` }} />
    </div>
  );
}

function CircularProgress({ pct, size = 120, stroke = 10 }) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  const color = pct <= 33 ? "#ef4444" : pct <= 66 ? "#f97316" : "#10b981";

  return (
    <svg width={size} height={size} className="block mx-auto">
      <defs>
        <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" floodColor="#000" floodOpacity="0.15" />
        </filter>
      </defs>
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
          style={{ filter: "url(#shadow)" }}
        />
        <foreignObject x={-(radius - 6)} y={-(radius - 6)} width={(radius - 6) * 2} height={(radius - 6) * 2}>
          <div className="flex flex-col items-center justify-center text-center p-2">
            <div className="text-sm text-gray-500">Saved</div>
            <div className="text-lg font-semibold text-gray-900">{pct}%</div>
          </div>
        </foreignObject>
      </g>
    </svg>
  );
}

export default function SavingsGoalsPage() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [active, setActive] = useState(null);
  const [mode, setMode] = useState("view");
  const [amountToAdd, setAmountToAdd] = useState("");
  const [error, setError] = useState(null);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadGoals();
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

  async function loadGoals() {
    setLoading(true);
    try {
      const data = await apiFetch("api/savings-goals/", {
        headers: getHeaders(),
      });
      setGoals(data);
      setError(null);
    } catch (err) {
      console.error("Failed to load savings goals", err?.message || err);
      setGoals([]);
      setError("Failed to load savings goals from server.");
    } finally {
      setLoading(false);
    }
  }

  function openModal(goal, initialMode = "view") {
    setActive(goal);
    setMode(initialMode);
    setAmountToAdd("");
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
    setActive(null);
    setMode("view");
  }

  async function handleAddSaving() {
    const amt = parseFloat(amountToAdd);
    if (Number.isNaN(amt) || amt <= 0) return alert("Enter a valid positive amount");

    const updated = goals.map((g) => (g.id === active.id ? { ...g, current_amount: (g.current_amount || 0) + amt } : g));
    setGoals(updated);
    setActive((prev) => (prev && prev.id === active.id ? { ...prev, current_amount: (prev.current_amount || 0) + amt } : prev));

    try {
      const data = await apiFetch(`api/savings-goals/${active.id}/add/`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ amount: amt }),
      });
      setGoals((prev) => prev.map((g) => (g.id === data.id ? data : g)));
      setActive(data);
    } catch (err) {
      console.warn("Add saving failed", err?.message || err);
      await loadGoals();
    }

    setAmountToAdd("");
    setMode("view");
  }

  async function handleCreateGoal(data) {
    setCreating(true);
    try {
      const goalData = await apiFetch("api/savings-goals/", {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(data),
      });
      setGoals((prev) => [goalData, ...(prev || [])]);
      setModalOpen(false);
      setMode("view");
      setActive(goalData);
    } catch (err) {
      console.error("Create goal failed", err?.message || err);
      alert("Failed to create goal");
    } finally {
      setCreating(false);
    }
  }

  async function handleEditGoal(changes) {
    const payload = {
      name: changes.name,
      target_amount: changes.target,
      description: changes.description,
    };

    const updated = goals.map((g) =>
      g.id === active.id ? { ...g, name: payload.name, target_amount: payload.target_amount, description: payload.description } : g
    );
    setGoals(updated);
    try {
      await apiFetch(`api/savings-goals/${active.id}/`, {
        method: "PUT",
        headers: getHeaders(),
        body: JSON.stringify(payload),
      });
    } catch (err) {
      console.warn("Edit goal failed", err?.message || err);
      await loadGoals();
    }
    setMode("view");
  }

  async function handleDeleteGoal() {
    if (!confirm("Delete this goal? This cannot be undone.")) return;
    const id = active.id;
    const prev = goals;
    setGoals(goals.filter((g) => g.id !== id));
    closeModal();
    try {
      await apiFetch(`api/savings-goals/${id}/`, {
        method: "DELETE",
        headers: getHeaders(),
      });
    } catch (err) {
      console.warn("Delete failed", err?.message || err);
      setGoals(prev);
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Savings Goals</h1>
        <div>
          <button
            onClick={() => {
              setMode("create");
              setActive(null);
              setModalOpen(true);
            }}
            className="px-3 py-2 bg-green-600 text-white rounded"
          >
            Add Goal
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">Loading...</div>
      ) : (
        <>
          {error && <div className="mb-4 text-sm text-red-600">{error}</div>}
          {goals.length === 0 ? (
            <div className="bg-white rounded shadow p-6 text-center">
              <div className="text-lg font-medium text-gray-700 mb-2">No savings goals yet</div>
              <div className="text-sm text-gray-500 mb-4">Create your first savings goal to start tracking progress.</div>
              <div>
                <button
                  onClick={() => {
                    setMode("create");
                    setActive(null);
                    setModalOpen(true);
                  }}
                  className="px-4 py-2 bg-green-600 text-white rounded"
                >
                  Create a goal
                </button>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {goals.map((g) => {
                const pct = Math.min(100, Math.round(((g.current_amount || 0) / (g.target_amount || 1)) * 100));
                return (
                  <div
                    key={g.id}
                    className="bg-white rounded shadow p-4 cursor-pointer hover:shadow-md flex flex-col"
                    onClick={() => openModal(g, "view")}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-sm text-gray-500">{g.name}</div>
                        <div className="text-lg font-semibold text-gray-900">${Number(g.current_amount || 0).toFixed(2)}</div>
                        <div className="text-xs text-gray-400">Target ${Number(g.target_amount || 0).toFixed(2)}</div>
                      </div>
                    </div>

                    <div className="mt-4">
                      <HorizontalProgress value={pct} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Modal */}
      {modalOpen && (active || mode === "create") && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg w-full max-w-xl p-6">
            <div className="flex items-start gap-6">
              {mode === "create" ? (
                <div className="w-full">
                  <h3 className="text-lg font-semibold mb-2">Create new goal</h3>
                  <CreateGoalForm
                    creating={creating}
                    onCancel={() => {
                      setModalOpen(false);
                      setMode("view");
                    }}
                    onSave={(payload) => handleCreateGoal(payload)}
                  />
                </div>
              ) : (
                <>
                  <div className="w-40 flex-shrink-0">
                    <CircularProgress pct={Math.min(100, Math.round(((active.current_amount || 0) / (active.target_amount || 1)) * 100))} />
                    <div className="text-center mt-2 text-sm text-gray-600">${Number(active.current_amount || 0).toFixed(2)} / ${Number(active.target_amount || 0).toFixed(2)}</div>
                  </div>

                  <div className="flex-1">
                    <h3 className="text-lg font-semibold">{active.name}</h3>
                    <p className="text-sm text-gray-500 mb-4">{active.description}</p>

                    {mode === "view" && (
                      <div className="flex gap-2">
                        <button onClick={() => setMode("add")} className="px-3 py-2 bg-green-500 text-white rounded">
                          Add Saving
                        </button>
                        <button onClick={() => setMode("edit")} className="px-3 py-2 bg-blue-600 text-white rounded">
                          Edit Goal
                        </button>
                        <button onClick={handleDeleteGoal} className="px-3 py-2 bg-red-600 text-white rounded">
                          Delete Goal
                        </button>
                        <button onClick={closeModal} className="px-3 py-2 border rounded ml-auto">
                          Close
                        </button>
                      </div>
                    )}

                    {mode === "add" && (
                      <div className="mt-4">
                        <label className="block text-sm mb-1">Amount</label>
                        <input
                          type="number"
                          step="0.01"
                          value={amountToAdd}
                          onChange={(e) => setAmountToAdd(e.target.value)}
                          className="w-full border rounded px-2 py-1 mb-3"
                        />
                        <div className="flex gap-2">
                          <button onClick={handleAddSaving} className="px-3 py-2 bg-green-500 text-white rounded">
                            Add
                          </button>
                          <button onClick={() => setMode("view")} className="px-3 py-2 border rounded">
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}

                    {mode === "edit" && (
                      <EditGoalForm goal={active} onCancel={() => setMode("view")} onSave={handleEditGoal} />
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function EditGoalForm({ goal, onCancel, onSave }) {
  const [name, setName] = useState(goal.name || "");
  const [target, setTarget] = useState(goal.target_amount || 0);
  const [description, setDescription] = useState(goal.description || "");

  return (
    <div className="mt-2">
      <label className="block text-sm mb-1">Name</label>
      <input value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded px-2 py-1 mb-2" />

      <label className="block text-sm mb-1">Target Amount</label>
      <input type="number" value={target} onChange={(e) => setTarget(parseFloat(e.target.value))} className="w-full border rounded px-2 py-1 mb-2" />

      <label className="block text-sm mb-1">Description</label>
      <input value={description} onChange={(e) => setDescription(e.target.value)} className="w-full border rounded px-2 py-1 mb-3" />

      <div className="flex gap-2">
        <button
          onClick={() => onSave({ name, target, description })}
          className="px-3 py-2 bg-blue-600 text-white rounded"
        >
          Save
        </button>
        <button onClick={onCancel} className="px-3 py-2 border rounded">
          Cancel
        </button>
      </div>
    </div>
  );
}

function CreateGoalForm({ creating, onCancel, onSave }) {
  const [name, setName] = useState("");
  const [target, setTarget] = useState(0);
  const [description, setDescription] = useState("");

  return (
    <div>
      <label className="block text-sm mb-1">Name</label>
      <input value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded px-2 py-1 mb-2" />

      <label className="block text-sm mb-1">Target Amount</label>
      <input type="number" value={target} onChange={(e) => setTarget(parseFloat(e.target.value) || 0)} className="w-full border rounded px-2 py-1 mb-2" />

      <label className="block text-sm mb-1">Description</label>
      <input value={description} onChange={(e) => setDescription(e.target.value)} className="w-full border rounded px-2 py-1 mb-3" />

      <div className="flex gap-2">
        <button
          onClick={() => onSave({ name, target_amount: target, description })}
          className="px-3 py-2 bg-green-600 text-white rounded"
          disabled={creating}
        >
          {creating ? "Creating..." : "Create"}
        </button>
        <button onClick={onCancel} className="px-3 py-2 border rounded">
          Cancel
        </button>
      </div>
    </div>
  );
}