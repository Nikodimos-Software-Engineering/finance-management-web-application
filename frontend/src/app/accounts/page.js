"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, getAuthHeaders } from "@/utils/api";

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
        <button 
          onClick={() => onEdit(a)} 
          className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm md:text-xs"
          aria-label={`Edit ${a.name}`}
        >
          Edit
        </button>
        <button 
          onClick={() => onDelete(a)} 
          className="px-3 py-1.5 bg-red-600 text-white rounded text-sm md:text-xs"
          aria-label={`Delete ${a.name}`}
        >
          Delete
        </button>
      </div>

      <div className="flex items-start gap-4">
        <div className="rounded-full w-12 h-12 md:w-10 md:h-10 flex-shrink-0 bg-gradient-to-br from-indigo-50 to-white flex items-center justify-center text-indigo-600 text-xl md:text-lg font-bold">
          {a.name?.slice(0,1) || 'A'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm text-gray-500 truncate">{a.name}</div>
          <div className="text-lg md:text-base font-semibold mt-1">{currency(a.balance)}</div>
          <div className="text-xs text-gray-400 mt-1">Created: {new Date(a.created_at).toLocaleDateString()}</div>
          {notes ? (
            <div className="text-sm text-gray-600 mt-2 line-clamp-2">{notes}</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default function AccountsPage() {
  const router = useRouter();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formName, setFormName] = useState("");
  const [formBalance, setFormBalance] = useState(0);
  const [formType, setFormType] = useState("checking");
  const [formNotes, setFormNotes] = useState("");
  const [notesMap, setNotesMap] = useState({});
  const [toDelete, setToDelete] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  
  // For pull-to-refresh on mobile
  const touchStartY = useRef(0);
  const [pullDownY, setPullDownY] = useState(0);
  const [showPullIndicator, setShowPullIndicator] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem("access")) {
      router.replace("/");
      return;
    }
    load();

    const handler = () => load();
    if (typeof window !== "undefined") {
      window.addEventListener("accounts:update", handler);
    }
    
    return () => {
      if (typeof window !== "undefined") window.removeEventListener("accounts:update", handler);
    };
  }, []);

  // Pull-to-refresh handlers for mobile
  const handleTouchStart = useCallback((e) => {
    if (window.scrollY === 0) {
      touchStartY.current = e.touches[0].clientY;
    }
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (touchStartY.current > 0 && window.scrollY === 0) {
      const currentY = e.touches[0].clientY;
      const diff = currentY - touchStartY.current;
      
      if (diff > 0) {
        setPullDownY(Math.min(diff, 100));
        setShowPullIndicator(diff > 50);
      }
    }
  }, []);

  const handleTouchEnd = useCallback(() => {
    if (showPullIndicator && !loading) {
      setRefreshing(true);
      load().finally(() => {
        setRefreshing(false);
        setShowPullIndicator(false);
      });
    }
    
    touchStartY.current = 0;
    setPullDownY(0);
    setTimeout(() => setShowPullIndicator(false), 300);
  }, [showPullIndicator, loading]);

  async function load() {
    setLoading(true);
    setError(null); 
    try {
      const data = await apiFetch("api/accounts/", {
        headers: getAuthHeaders(),
      });
      setAccounts(data || []);
    } catch (err) {
      console.error("Failed to load accounts:", err);
      setError(`Failed to load accounts: ${err.status || 'Network error'}`);
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditing(null);
    setFormName("");
    setFormBalance(0);
    setFormType("checking");
    setFormNotes("");
    setModalOpen(true);
  }

  function openEdit(a) {
    setEditing(a);
    setFormName(a.name || "");
    setFormBalance(Number(a.balance || 0));
    setFormType(a.account_type || "checking");
    setFormNotes(notesMap[a.id] || "");
    setModalOpen(true);
  }

  async function handleSave() {
    if (!formName.trim()) return alert("Enter account name");
    setSaving(true);
    try {
      const payload = { name: formName.trim(), balance: formBalance, account_type: formType };
      if (editing) {
        const data = await apiFetch(`api/accounts/${editing.id}`, {
          method: "PUT",
          headers: getAuthHeaders(),
          body: JSON.stringify(payload),
        });
        setAccounts((prev) => prev.map((p) => (p.id === data.id ? data : p)));
        setNotesMap((n) => ({ ...n, [data.id]: formNotes }));
      } else {
        const data = await apiFetch("api/accounts/", {
          method: "POST",
          headers: getAuthHeaders(),
          body: JSON.stringify(payload),
        });
        setAccounts((prev) => [data, ...(prev || [])]);
        setNotesMap((n) => ({ ...n, [data.id]: formNotes }));
      }
      setModalOpen(false);
    } catch (err) {
      console.error("Failed to save account:", err);
      alert(`Failed to save account: ${err.status || 'Network error'}`);
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
      await apiFetch(`api/accounts/${toDelete.id}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      setNotesMap((n) => {
        const nxt = { ...n };
        delete nxt[toDelete.id];
        return nxt;
      });
    } catch (err) {
      console.error("Failed to delete account:", err);
      setAccounts(prev);
      alert(`Failed to delete account: ${err.status || 'Network error'}`);
    }
  }

  const totalBalance = accounts.reduce((s, a) => s + Number(a.balance || 0), 0);

  return (
    <div 
      className="min-h-screen bg-gray-50"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull-to-refresh indicator */}
      <div 
        className="fixed top-0 left-0 right-0 flex justify-center items-center transition-transform duration-200 z-40"
        style={{ 
          transform: `translateY(${pullDownY}px)`,
          height: '60px',
          pointerEvents: 'none'
        }}
      >
        {showPullIndicator ? (
          <div className="bg-blue-100 text-blue-700 px-4 py-2 rounded-full shadow flex items-center gap-2">
            <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm font-medium">Release to refresh</span>
          </div>
        ) : null}
      </div>

      <div className="p-4 md:p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 md:mb-6 gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Accounts</h1>
            <p className="text-sm text-gray-500 mt-1">Manage your cash, bank, and digital accounts</p>
          </div>
          <button
            onClick={() => load()}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm font-medium flex items-center gap-2 self-start md:self-center"
            disabled={loading || refreshing}
          >
            <svg className={`w-4 h-4 ${loading || refreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            {loading || refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <SummaryCard title="Total Accounts" value={accounts.length} icon="🏦" />
          <SummaryCard title="Total Balance" value={currency(totalBalance)} icon="💳" />
        </div>

        {loading && !refreshing ? (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <div className="text-sm text-gray-500">Loading accounts...</div>
          </div>
        ) : (
          <div className="grid gap-4 grid-cols-1">
            {accounts.map((a) => (
              <AccountCard key={a.id} a={a} onEdit={openEdit} onDelete={confirmDelete} notes={notesMap[a.id]} />
            ))}
            {accounts.length === 0 && !error && (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">🏦</div>
                <div className="text-lg font-medium text-gray-700 mb-2">No accounts yet</div>
                <div className="text-sm text-gray-500 mb-6">Add your first account to get started</div>
                <button
                  onClick={openCreate}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
                >
                  Add Your First Account
                </button>
              </div>
            )}
          </div>
        )}

        {/* Floating add button - hidden on mobile when modal is open */}
        {!modalOpen && !confirmOpen && (
          <button
            onClick={openCreate}
            className="fixed right-4 bottom-4 md:right-8 md:bottom-8 bg-blue-600 text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg hover:scale-105 transition active:scale-95 z-30"
            aria-label="Add account"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path>
            </svg>
          </button>
        )}
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="p-4 md:p-6">
              <h3 className="text-lg font-semibold mb-3">{editing ? "Edit Account" : "Add Account"}</h3>
              <div className="grid gap-3">
                <div>
                  <label className="block text-sm mb-1 font-medium">Account name *</label>
                  <input 
                    value={formName} 
                    onChange={(e) => setFormName(e.target.value)} 
                    className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    placeholder="e.g., Chase Checking"
                    autoFocus
                  />
                </div>

                <div>
                  <label className="block text-sm mb-1 font-medium">Initial balance *</label>
                  <input 
                    type="number" 
                    step="0.01" 
                    value={formBalance} 
                    onChange={(e) => setFormBalance(e.target.value)} 
                    className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="block text-sm mb-1 font-medium">Account type</label>
                  <select
                    value={formType}
                    onChange={(e) => setFormType(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  >
                    <option value="checking">Checking</option>
                    <option value="savings">Savings</option>
                    <option value="credit">Credit Card</option>
                    <option value="cash">Cash</option>
                    <option value="investment">Investment</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm mb-1 font-medium">Notes (optional)</label>
                  <textarea 
                    value={formNotes} 
                    onChange={(e) => setFormNotes(e.target.value)} 
                    className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    rows="3"
                    placeholder="Add any notes about this account..."
                  />
                  <div className="text-xs text-gray-500 mt-1">Notes are stored locally on your device</div>
                </div>

                <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 mt-4 pt-4 border-t">
                  <button 
                    onClick={() => { setModalOpen(false); setEditing(null); }} 
                    className="px-4 py-2.5 border rounded-lg font-medium hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={handleSave} 
                    className="px-4 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed" 
                    disabled={saving || !formName.trim()}
                  >
                    {saving ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Saving...
                      </span>
                    ) : 'Save'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirm delete modal */}
      {confirmOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-sm">
            <div className="p-4 md:p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                  <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.998-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                  </svg>
                </div>
                <h3 className="text-lg font-semibold">Delete account?</h3>
              </div>
              
              <p className="text-sm text-gray-600 mb-2">
                Are you sure you want to delete <span className="font-medium">{toDelete?.name}</span>?
              </p>
              <p className="text-xs text-gray-500 mb-6">
                This account will be removed permanently. Any existing transactions will remain but will no longer be associated with this account.
              </p>
              
              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2">
                <button 
                  onClick={() => setConfirmOpen(false)} 
                  className="px-4 py-2.5 border rounded-lg font-medium hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleDelete} 
                  className="px-4 py-2.5 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition"
                >
                  Delete Account
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}