"use client";

import React, { useEffect, useState } from "react";
import axios from "axios";

const api = axios.create({ baseURL: "/api" });
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access");
    if (token) config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

function currency(n) {
  return `$${Number(n || 0).toFixed(2)}`;
}

function SummaryCard({ title, value, icon }) {
  return (
    <div className="p-4 rounded-lg shadow-sm transform transition hover:-translate-y-1 bg-gradient-to-r from-white to-gray-50">
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">{title}</div>
        <div className="text-2xl">{icon}</div>
      </div>
      <div className="mt-3 text-xl font-semibold">{value}</div>
    </div>
  );
}

function AccountCard({ a, onEdit, onDelete, notes }) {
  return (
    <div className="bg-white rounded-lg p-4 shadow hover:shadow-md transition relative">
      <div className="absolute right-3 top-3 flex gap-2">
        <button onClick={() => onEdit(a)} className="px-2 py-1 bg-blue-600 text-white rounded text-xs">Edit</button>
        <button onClick={() => onDelete(a)} className="px-2 py-1 bg-red-600 text-white rounded text-xs">Delete</button>
      </div>

      <div className="flex items-start gap-4">
        <div className="rounded-full w-12 h-12 bg-gradient-to-br from-indigo-50 to-white flex items-center justify-center text-indigo-600 text-xl font-bold">
          {a.name?.slice(0,1) || 'A'}
        </div>
        <div className="flex-1">
          <div className="text-sm text-gray-500">{a.name}</div>
          <div className="text-lg font-semibold mt-1">{currency(a.balance)}</div>
          <div className="text-xs text-gray-400 mt-1">Created: {new Date(a.created_at).toLocaleDateString()}</div>
          {notes ? <div className="text-sm text-gray-600 mt-2">{notes}</div> : null}
        </div>
      </div>
    </div>
  );
}

export default function AccountsPage() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formName, setFormName] = useState("");
  const [formBalance, setFormBalance] = useState(0);
  const [formNotes, setFormNotes] = useState("");
  const [notesMap, setNotesMap] = useState({});
  const [toDelete, setToDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    load();

    const handler = () => load();
    if (typeof window !== "undefined") {
      window.addEventListener("accounts:update", handler);
    }
    // periodic refresh as fallback
    const int = setInterval(() => load(), 15000);
    return () => {
      if (typeof window !== "undefined") window.removeEventListener("accounts:update", handler);
      clearInterval(int);
    };
  }, []);

  async function load() {
    setLoading(true);
    try {
      const res = await api.get("/accounts/");
      setAccounts(res.data || []);
    } catch (err) {
      console.error(err);
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditing(null);
    setFormName("");
    setFormBalance(0);
    setFormNotes("");
    setModalOpen(true);
  }

  function openEdit(a) {
    setEditing(a);
    setFormName(a.name || "");
    setFormBalance(Number(a.balance || 0));
    setFormNotes(notesMap[a.id] || "");
    setModalOpen(true);
  }

  async function handleSave() {
    if (!formName) return alert("Enter account name");
    if (Number(formBalance) === 0 && formBalance !== 0 && formBalance !== "") return alert("Enter a valid balance");
    setSaving(true);
    try {
      if (editing) {
        const payload = { name: formName, balance: formBalance };
        const res = await api.put(`/accounts/${editing.id}/`, payload);
        setAccounts((prev) => prev.map((p) => (p.id === res.data.id ? res.data : p)));
        setNotesMap((n) => ({ ...n, [res.data.id]: formNotes }));
      } else {
        const payload = { name: formName, balance: formBalance };
        const res = await api.post(`/accounts/`, payload);
        setAccounts((prev) => [res.data, ...(prev || [])]);
        setNotesMap((n) => ({ ...n, [res.data.id]: formNotes }));
      }
      setModalOpen(false);
    } catch (err) {
      console.error(err);
      alert("Failed to save account");
    } finally {
      setSaving(false);
    }
  }

  function confirmDelete(a) {
    setToDelete(a);
    setConfirmOpen(true);
  }

  async function handleDelete() {
    if (!toDelete) return;
    const prev = accounts;
    setAccounts(prev.filter((x) => x.id !== toDelete.id));
    setConfirmOpen(false);
    try {
      await api.delete(`/accounts/${toDelete.id}/`);
      setNotesMap((n) => {
        const nxt = { ...n };
        delete nxt[toDelete.id];
        return nxt;
      });
    } catch (err) {
      console.error(err);
      setAccounts(prev);
      alert("Failed to delete account");
    }
  }

  const totalBalance = accounts.reduce((s, a) => s + Number(a.balance || 0), 0);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">Accounts</h1>
      <p className="text-sm text-gray-500 mt-1 mb-6">Manage your cash, bank, and digital accounts here.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <SummaryCard title="Total Accounts" value={accounts.length} icon="🏦" />
        <SummaryCard title="Total Balance" value={currency(totalBalance)} icon="💳" />
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">Loading accounts...</div>
      ) : (
        <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
          {accounts.map((a) => (
            <AccountCard key={a.id} a={a} onEdit={openEdit} onDelete={confirmDelete} notes={notesMap[a.id]} />
          ))}
          {accounts.length === 0 && <div className="text-sm text-gray-500">No accounts yet. Add one using the + button.</div>}
        </div>
      )}

      {/* Floating add button */}
      <button
        onClick={openCreate}
        className="fixed right-8 bottom-8 bg-blue-600 text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg hover:scale-105 transition"
        aria-label="Add account"
      >
        +
      </button>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-md p-6">
            <h3 className="text-lg font-semibold mb-3">{editing ? "Edit Account" : "Add Account"}</h3>
            <div className="grid gap-3">
              <label className="text-sm">Account name</label>
              <input value={formName} onChange={(e) => setFormName(e.target.value)} className="w-full border rounded px-2 py-1" />

              <label className="text-sm">Initial balance</label>
              <input type="number" step="0.01" value={formBalance} onChange={(e) => setFormBalance(e.target.value)} className="w-full border rounded px-2 py-1" />

              <label className="text-sm">Notes (local only)</label>
              <textarea value={formNotes} onChange={(e) => setFormNotes(e.target.value)} className="w-full border rounded px-2 py-1" />

              <div className="flex justify-end gap-2 mt-3">
                <button onClick={() => { setModalOpen(false); setEditing(null); }} className="px-3 py-2 border rounded">Cancel</button>
                <button onClick={handleSave} className="px-3 py-2 bg-blue-600 text-white rounded" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirm delete */}
      {confirmOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-sm p-6">
            <h3 className="text-lg font-semibold mb-3">Delete account?</h3>
            <p className="text-sm text-gray-600">This will remove the account. Transactions tied to it are unaffected on the server side.</p>
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setConfirmOpen(false)} className="px-3 py-2 border rounded">Cancel</button>
              <button onClick={handleDelete} className="px-3 py-2 bg-red-600 text-white rounded">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
