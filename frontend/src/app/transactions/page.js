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

async function fetchAccounts() {
  const res = await api.get("/accounts/");
  return res.data;
}

async function fetchCategories() {
  const res = await api.get("/categories/");
  return res.data;
}

async function fetchTransactions() {
  const res = await api.get("/transactions/");
  return res.data;
}

async function fetchBudgets() {
  const res = await api.get("/budgets/");
  return res.data;
}

async function createTransaction(payload) {
  return (await api.post("/transactions/", payload)).data;
}

async function updateTransaction(id, payload) {
  return (await api.put(`/transactions/${id}/`, payload)).data;
}

async function deleteTransaction(id) {
  return (await api.delete(`/transactions/${id}/`)).data;
}

function FilterPanel({ accounts, filters, setFilters }) {
  return (
    <div className="p-4 bg-white rounded shadow">
      <h3 className="font-semibold mb-3">Filters</h3>
      <div className="mb-3">
        <label className="block text-sm mb-1">Account</label>
        <select
          value={filters.account || ""}
          onChange={(e) => setFilters((s) => ({ ...s, account: e.target.value || null }))}
          className="w-full border rounded px-2 py-1"
        >
          <option value="">All accounts</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>
      </div>
      <div className="mb-3">
        <label className="block text-sm mb-1">Category type</label>
        <select
          value={filters.type || ""}
          onChange={(e) => setFilters((s) => ({ ...s, type: e.target.value || null }))}
          className="w-full border rounded px-2 py-1"
        >
          <option value="">All</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
      </div>
      <div className="mb-3">
        <label className="block text-sm mb-1">Date from</label>
        <input
          type="date"
          value={filters.date_after || ""}
          onChange={(e) => setFilters((s) => ({ ...s, date_after: e.target.value || null }))}
          className="w-full border rounded px-2 py-1"
        />
      </div>
      <div className="mb-3">
        <label className="block text-sm mb-1">Date to</label>
        <input
          type="date"
          value={filters.date_before || ""}
          onChange={(e) => setFilters((s) => ({ ...s, date_before: e.target.value || null }))}
          className="w-full border rounded px-2 py-1"
        />
      </div>
      <button onClick={() => setFilters({})} className="mt-2 w-full bg-gray-200 text-sm py-2 rounded">
        Clear
      </button>
    </div>
  );
}

function TransactionItem({ tx, onDelete, onEdit }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b py-3">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setOpen((v) => !v)}
      >
        <div className="flex justify-between w-full text-sm">
          <span className="w-1/3 font-medium">{tx.category.type.toUpperCase()}</span>
          <span className="w-1/3">{tx.category.name}</span>
          <span
            className={`w-1/3 text-right font-semibold ${
              tx.category.type === "income" ? "text-green-600" : "text-red-600"
            }`}
          >
            {tx.amount}
          </span>
        </div>
      </div>

      {open && (
        <div className="flex justify-between mt-2 text-sm text-gray-700 items-center">
          <div className="flex flex-col gap-1">
            <div><strong>Account:</strong> {tx.account.name}</div>
            <div><strong>Date:</strong> {tx.date}</div>
            <div><strong>Description:</strong> {tx.description || "—"}</div>
          </div>
          <div className="flex flex-col gap-2">
            <button
              onClick={() => onEdit(tx)}
              className="px-3 py-1 bg-blue-600 text-white rounded text-sm"
            >
              Edit
            </button>
            <button
              onClick={() => {
                if (confirm("Are you sure you want to delete this transaction?")) onDelete(tx);
              }}
              className="px-3 py-1 bg-red-600 text-white rounded text-sm"
            >
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function TransactionList({ transactions, onDelete, onEdit }) {
  if (!transactions || transactions.length === 0)
    return <div className="p-4 text-sm text-gray-500">No transactions</div>;

  return (
    <div>
      {transactions.map((tx) => (
        <TransactionItem key={tx.id} tx={tx} onDelete={onDelete} onEdit={onEdit} />
      ))}
    </div>
  );
}

function AddTransactionModal({ isOpen, onClose, onSave, accounts, categories, budgets, initial }) {
  const [form, setForm] = useState({
    account: "",
    category: "",
    description: "",
    date: "",
    amount: "",
    budget: "",
  });
  const [type, setType] = useState("expense"); // default type = expense

  useEffect(() => {
    if (initial) {
      setForm({
        account: initial.account.id,
        category: initial.category.id,
        description: initial.description || "",
        date: initial.date || "",
        amount: initial.amount || "",
        budget: initial.budget?.id || "",
      });
      setType(initial.category?.type || "expense");
    } else {
      setForm({ account: "", category: "", description: "", date: "", amount: "" });
      setType("expense");
    }
  }, [initial, isOpen]);

  const filteredCategories = categories.filter((c) => c.type === type);
  // budgets filtered by selected category
  const budgetsForCategory = (budgets || []).filter((b) => String(b.category?.id) === String(form.category));

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((s) => ({ ...s, [name]: value }));
  };

  const handleTypeChange = (e) => {
    const newType = e.target.value;
    setType(newType);
    setForm((s) => ({ ...s, category: "" }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      account: form.account,
      category: form.category,
      description: form.description,
      date: form.date,
      amount: form.amount,
      budget: form.budget || null,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white w-full max-w-lg p-6 rounded">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium">{initial ? "Edit Transaction" : "Add Transaction"}</h3>
          <button onClick={onClose} className="text-gray-600">Close</button>
        </div>
        <form onSubmit={handleSubmit} className="grid gap-3">
          <div>
            <label className="block text-sm mb-1">Type</label>
            <div className="flex gap-3">
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="type"
                  value="income"
                  checked={type === "income"}
                  onChange={handleTypeChange}
                  className="mr-2"
                />
                Income
              </label>
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="type"
                  value="expense"
                  checked={type === "expense"}
                  onChange={handleTypeChange}
                  className="mr-2"
                />
                Expense
              </label>
            </div>
          </div>
          <div>
            <label className="block text-sm mb-1">Account</label>
            <select
              name="account"
              value={form.account}
              onChange={handleChange}
              className="w-full border rounded px-2 py-1"
            >
              <option value="">Select account</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
          </div>

          {type && (<>
            <div>
              <label className="block text-sm mb-1">Category</label>
              <select
                name="category"
                value={form.category}
                onChange={handleChange}
                className="w-full border rounded px-2 py-1"
              >
                <option value="">Select category</option>
                {filteredCategories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            {type === "expense" && form.category && (
              <div>
                <label className="block text-sm mb-1">Budget (optional)</label>
                <select name="budget" value={form.budget} onChange={handleChange} className="w-full border rounded px-2 py-1">
                  <option value="">-- No budget --</option>
                  {budgetsForCategory.map((b) => (
                    <option key={b.id} value={b.id}>{b.category?.name} — {b.allocated_amount}</option>
                  ))}
                </select>
              </div>
            )}
          </>)}

          <div>
            <label className="block text-sm mb-1">Date</label>
            <input
              type="date"
              name="date"
              value={form.date}
              onChange={handleChange}
              className="w-full border rounded px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Amount</label>
            <input
              type="number"
              step="0.01"
              name="amount"
              value={form.amount}
              onChange={handleChange}
              className="w-full border rounded px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Description</label>
            <input
              type="text"
              name="description"
              value={form.description}
              onChange={handleChange}
              className="w-full border rounded px-2 py-1"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function TransactionsPage() {
  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [filters, setFilters] = useState({});
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [page, setPage] = useState(1);
  const [allTransactions, setAllTransactions] = useState([]);

  const itemsPerPage = 5;
  const paginated = transactions.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  useEffect(() => {
    loadMeta();
    loadTransactions();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [filters]);

  async function loadMeta() {
    try {
      const [accs, cats, buds] = await Promise.all([fetchAccounts(), fetchCategories(), fetchBudgets()]);
      setAccounts(accs);
      setCategories(cats);
      setBudgets(buds || []);
    } catch (err) {
      console.error(err);
    }
  }

  function doFilter(list, filters) {
    if (!list) return [];
    return list.filter((tx) => {
      // account filter
      if (filters.account) {
        const accId = tx.account?.id != null ? String(tx.account.id) : String(tx.account);
        if (accId !== String(filters.account)) return false;
      }

      // type filter (income/expense)
      if (filters.type) {
        if (tx.category?.type !== filters.type) return false;
      }

      // date range filters (inclusive)
      if (filters.date_after) {
        const txDate = new Date(tx.date);
        const afterDate = new Date(filters.date_after);
        if (txDate < afterDate) return false;
      }
      if (filters.date_before) {
        const txDate = new Date(tx.date);
        const beforeDate = new Date(filters.date_before);
        if (txDate > beforeDate) return false;
      }

      return true;
    });
  }

  function applyFilters() {
    const filtered = doFilter(allTransactions, filters);
    setTransactions(filtered);
    setPage(1);
  }

  async function loadTransactions() {
    setLoading(true);
    try {
      const data = await fetchTransactions();
      setAllTransactions(data || []);
      setTransactions(doFilter(data || [], filters));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const handleCreate = async (payload) => {
    const body = {
      account_id: payload.account,
      category_id: payload.category,
      description: payload.description,
      date: payload.date,
      amount: payload.amount,
      // include optional budget selection
      ...(payload.budget ? { budget_id: payload.budget } : {}),
    };
    try {
      const created = await createTransaction(body);
      setAllTransactions((prev) => {
        const next = [created, ...prev];
        setTransactions(doFilter(next, filters));
        return next;
      });
      // refresh budgets so remaining_amount updates in UI
      try {
        const newB = await fetchBudgets();
        setBudgets(newB || []);
      } catch (err) {
        console.warn("Failed to refresh budgets", err);
      }
      setIsOpen(false);
      setPage(1);
      // notify other pages (accounts) to refresh balances
      try {
        if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("accounts:update"));
      } catch (e) {
        // ignore
      }
    } catch {
      alert("Failed to create transaction");
    }
  };

  const handleDelete = async (tx) => {
    try {
      await deleteTransaction(tx.id);
      setAllTransactions((prev) => {
        const next = prev.filter((t) => t.id !== tx.id);
        setTransactions(doFilter(next, filters));
        return next;
      });
      // refresh budgets
      try {
        const newB = await fetchBudgets();
        setBudgets(newB || []);
      } catch (err) {
        console.warn("Failed to refresh budgets", err);
      }
      // notify accounts to refresh balances
      try {
        if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("accounts:update"));
      } catch (e) {}
    } catch {
      alert("Failed to delete transaction");
    }
  };

  const handleEdit = (tx) => {
    setEditing(tx);
    setIsOpen(true);
  };

  const handleSaveEdit = async (payload) => {
    const body = {
      account_id: payload.account,
      category_id: payload.category,
      description: payload.description,
      date: payload.date,
      amount: payload.amount,
      ...(payload.budget ? { budget_id: payload.budget } : {}),
    };
    try {
      const updated = await updateTransaction(editing.id, body);
      setAllTransactions((prev) => {
        const next = prev.map((t) => (t.id === updated.id ? updated : t));
        setTransactions(doFilter(next, filters));
        return next;
      });
      // refresh budgets after update
      try {
        const newB = await fetchBudgets();
        setBudgets(newB || []);
      } catch (err) {
        console.warn("Failed to refresh budgets", err);
      }
      setEditing(null);
      setIsOpen(false);
      // notify accounts to refresh balances
      try {
        if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("accounts:update"));
      } catch (e) {}
    } catch {
      alert("Failed to update transaction");
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Transactions</h1>
      <div className="grid md:grid-cols-4 gap-4">
        <div className="md:col-span-1">
          <FilterPanel accounts={accounts} filters={filters} setFilters={setFilters} />
        </div>
        <div className="md:col-span-3 bg-white rounded shadow p-4 relative">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-medium">Recent transactions</h2>
            <button
              onClick={() => {
                setEditing(null);
                setIsOpen(true);
              }}
              className="bg-blue-600 text-white px-3 py-1 rounded"
            >
              +
            </button>
          </div>
          {loading ? (
            <div className="text-sm text-gray-500">Loading...</div>
          ) : (
            <TransactionList transactions={paginated} onDelete={handleDelete} onEdit={handleEdit} />
          )}
        </div>
      </div>

      {/* Pagination moved below the box */}
      <div className="flex justify-between ml-[330px] mt-3 text-sm bg-white shadow rounded p-3 w-full md:w-3/4 mx-auto">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          Prev
        </button>
        <span>
          Page {page} of {Math.ceil(transactions.length / itemsPerPage)}
        </span>
        <button
          onClick={() =>
            setPage((p) => (p < Math.ceil(transactions.length / itemsPerPage) ? p + 1 : p))
          }
          disabled={page >= Math.ceil(transactions.length / itemsPerPage)}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          Next
        </button>
      </div>

      <AddTransactionModal
        isOpen={isOpen}
        onClose={() => {
          setIsOpen(false);
          setEditing(null);
        }}
        onSave={(payload) => (editing ? handleSaveEdit(payload) : handleCreate(payload))}
        accounts={accounts}
        categories={categories}
        budgets={budgets}
        initial={editing}
      />
    </div>
  );
}
