"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/utils/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const COLORS = ["#60a5fa", "#34d399", "#f59e0b", "#f87171", "#a78bfa", "#fbbf24"];

function StatCard({ title, value, icon, onClick }) {
  return (
    <div onClick={onClick} className="p-4 rounded-lg shadow-sm transform hover:-translate-y-1 bg-gradient-to-r from-white to-gray-50 cursor-pointer">
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">{title}</div>
        <div className="text-2xl">{icon}</div>
      </div>
      <div className="mt-3 text-xl font-semibold">{value}</div>
    </div>
  );
}

function MiniTxn({ tx }) {
  const isIncome = tx.category?.type === "income";
  return (
    <div className="flex justify-between py-2 border-b last:border-b-0">
      <div>
        <div className="text-sm font-medium">{tx.category?.name}</div>
        <div className="text-xs text-gray-500">{tx.date}</div>
      </div>
      <div className={isIncome ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>{Number(tx.amount).toFixed(2)}</div>
    </div>
  );
}

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

async function fetchAccounts() {
  const data = await apiFetch("api/accounts/", {
    headers: getHeaders(),
  });
  return data;
}

async function fetchTransactions() {
  const data = await apiFetch("api/transactions/", {
    headers: getHeaders(),
  });
  return data;
}

async function fetchBudgets() {
  const data = await apiFetch("api/budgets/", {
    headers: getHeaders(),
  });
  return data;
}

async function fetchSavingsGoals() {
  const data = await apiFetch("api/savings-goals/", {
    headers: getHeaders(),
  });
  return data;
}

export default function DashboardPage() {
  const router = useRouter();
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [savings, setSavings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [userName, setUserName] = useState("");

  useEffect(() => {
    loadAll();
    try {
      if (typeof window !== "undefined") {
        const raw = localStorage.getItem("user");
        if (raw) {
          const parsed = JSON.parse(raw);
          const name = [parsed.first_name, parsed.last_name].filter(Boolean).join(" ") || parsed.username || "";
          setUserName(name);
        }
        else{
          router.replace("/")
        }
      }
    } catch (e) {
      // ignore
    }
  }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [accData, txData, bdData, svData] = await Promise.all([
        fetchAccounts(),
        fetchTransactions(),
        fetchBudgets(),
        fetchSavingsGoals(),
      ]);
      setAccounts(accData || []);
      setTransactions((txData || []).sort((a, b) => (a.date < b.date ? 1 : -1)));
      setBudgets(bdData || []);
      setSavings(svData || []);
    } catch (err) {
      console.warn("Dashboard load failed, using empty data", err);
      setAccounts([]);
      setTransactions([]);
      setBudgets([]);
      setSavings([]);
    } finally {
      setLoading(false);
    }
  }

  const totalBalance = useMemo(() => accounts.reduce((s, a) => s + Number(a.balance || 0), 0), [accounts]);

  function lastNMonths(n = 6) {
    const res = [];
    const now = new Date();
    for (let i = n - 1; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      res.push(d.toISOString().slice(0, 7));
    }
    return res;
  }

  const months = useMemo(() => lastNMonths(6), []);

  const monthlySeries = useMemo(() => {
    const m = months.map((mon) => ({ month: mon, income: 0, expense: 0 }));
    (transactions || []).forEach((t) => {
      if (!t.date) return;
      const key = t.date.slice(0, 7);
      const idx = m.findIndex((x) => x.month === key);
      if (idx === -1) return;
      if (t.category?.type === "income") m[idx].income += Number(t.amount || 0);
      else m[idx].expense += Math.abs(Number(t.amount || 0));
    });
    return m;
  }, [transactions, months]);

  const expenseByCategory = useMemo(() => {
    const map = {};
    (transactions || []).forEach((t) => {
      if (t.category?.type === "expense") {
        const name = t.category?.name || "Unknown";
        map[name] = (map[name] || 0) + Math.abs(Number(t.amount || 0));
      }
    });
    return Object.entries(map).map(([name, value]) => ({ name, value }));
  }, [transactions]);

  const totalIncomeThisMonth = useMemo(() => {
    const month = new Date().toISOString().slice(0, 7);
    return transactions.filter((t) => t.date?.slice(0, 7) === month && t.category?.type === "income").reduce((s, t) => s + Number(t.amount || 0), 0);
  }, [transactions]);

  const totalExpenseThisMonth = useMemo(() => {
    const month = new Date().toISOString().slice(0, 7);
    return transactions.filter((t) => t.date?.slice(0, 7) === month && t.category?.type === "expense").reduce((s, t) => s + Math.abs(Number(t.amount || 0)), 0);
  }, [transactions]);

  const totalRemainingBudget = useMemo(() => (budgets || []).reduce((s, b) => s + Number(b.remaining_amount || 0), 0), [budgets]);

  const top3 = transactions.slice(0, 3);

  const savingsTotal = useMemo(() => (savings || []).reduce((s, g) => s + Number(g.current_amount || 0), 0), [savings]);
  const savingsTargetTotal = useMemo(() => (savings || []).reduce((s, g) => s + Number(g.target_amount || 0), 0), [savings]);

  const alertBudgetPct = useMemo(() => {
    const totalBudgeted = (budgets || []).reduce((s, b) => s + Number(b.allocated_amount || 0), 0);
    const totalRemaining = (budgets || []).reduce((s, b) => s + Number(b.remaining_amount || 0), 0);
    const spent = totalBudgeted - totalRemaining;
    return totalBudgeted ? (spent / totalBudgeted) * 100 : 0;
  }, [budgets]);

  function doLogout() {
    try {
      if (typeof window !== "undefined") localStorage.clear();
    } catch (e) {
      console.warn("logout clear failed", e);
    }
    router.push("/");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar: fixed to left and top */}
      <aside className="fixed left-0 top-0 w-64 h-screen bg-white border-r p-4 flex flex-col justify-between z-40">
        <div>
          <div className="text-xl font-semibold mb-6">Budget Tracker</div>
          <nav className="flex flex-col gap-2">
            <button onClick={() => router.push('/transactions')} className="text-left px-3 py-2 rounded hover:bg-gray-100">💸 Transactions</button>
            <button onClick={() => router.push('/budget')} className="text-left px-3 py-2 rounded hover:bg-gray-100">💼 Budgets</button>
            <button onClick={() => router.push('/savings-goals')} className="text-left px-3 py-2 rounded hover:bg-gray-100">🥅 Savings Goals</button>
            <button onClick={() => router.push('/accounts')} className="text-left px-3 py-2 rounded hover:bg-gray-100">💳 Accounts</button>
          </nav>
        </div>
        <div className="text-sm">
          <button onClick={() => router.push('/profile')} className="w-full text-left px-3 py-2 rounded hover:bg-gray-100">👤 Profile</button>
          <button onClick={() => setShowLogoutConfirm(true)} className="w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-rose-600">Logout</button>
        </div>
      </aside>

      {/* Navbar: fixed to top, starting right after the sidebar */}
      <header className="fixed top-0 left-64 right-0 h-14 bg-white shadow-sm z-30 flex items-center px-6">
        <div className="flex-1 text-sm text-gray-700">Hello, {userName || "User"}</div>
        <div className="text-sm text-gray-500">Dashboard</div>
      </header>


      {/* Main content area: offset by sidebar width and navbar height; this area scrolls */}
      <main className="ml-64 pt-14 p-6" style={{ minHeight: 'calc(100vh - 56px)' }}>
        <div className="space-y-6">
          {/* Overview cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard title="Total Balance" value={`$${Number(totalBalance).toFixed(2)}`} icon="💰" onClick={() => router.push('/accounts')} />
            <StatCard title="Total Income (This month)" value={`$${Number(totalIncomeThisMonth).toFixed(2)}`} icon="📈" onClick={() => router.push('/transactions')} />
            <StatCard title="Total Expenses (This month)" value={`$${Number(totalExpenseThisMonth).toFixed(2)}`} icon="📉" onClick={() => router.push('/transactions')} />
            <StatCard title="Remaining Budget" value={`$${Number(totalRemainingBudget).toFixed(2)}`} icon="🧾" onClick={() => router.push('/budget')} />
          </div>

          {/* Two stacked sections */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white rounded shadow p-4">
              <div className="flex items-start justify-between">
                <h3 className="font-semibold">Recent transactions</h3>
                <button onClick={() => router.push('/transactions')} className="text-sm px-2 py-1 border rounded">View All</button>
              </div>
              <div className="mt-3">
                <div className="flex gap-4 mb-3">
                  {alertBudgetPct > 90 && (
                    <div className="p-3 bg-rose-50 rounded border-l-4 border-rose-400 text-sm text-rose-700">Alert: Expenses &gt; 90% of budgets</div>
                  )}
                </div>
                <div className="divide-y">
                  {top3.length === 0 && <div className="text-sm text-gray-500">No recent transactions</div>}
                  {top3.map((t) => (
                    <MiniTxn key={t.id} tx={t} />
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-white rounded shadow p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Savings Progress</div>
                  <div className="text-xs text-gray-500">Total saved vs goals</div>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                  <div className="h-3 bg-green-400 rounded-full" style={{ width: `${savingsTargetTotal ? Math.min(100, (savingsTotal / savingsTargetTotal) * 100) : 0}%` }} />
                </div>
                <div className="text-sm mt-2">${Number(savingsTotal).toFixed(2)} saved of ${Number(savingsTargetTotal).toFixed(2)}</div>
              </div>

              <div className="bg-white rounded shadow p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Next savings goal</div>
                  <div className="text-xs text-gray-500">Almost there</div>
                </div>
                {savings.length === 0 ? (
                  <div className="text-sm text-gray-500">No savings goals</div>
                ) : (
                  (() => {
                    const next = savings.map((s) => ({ ...s, pct: s.target_amount ? (s.current_amount / s.target_amount) * 100 : 0 })).sort((a, b) => b.pct - a.pct)[0];
                    return (
                      <div>
                        <div className="text-sm font-semibold">{next.name}</div>
                        <div className="text-xs text-gray-500">{next.description}</div>
                        <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden mt-3">
                          <div className="h-3 bg-indigo-400 rounded-full" style={{ width: `${Math.min(100, next.pct)}%` }} />
                        </div>
                        <div className="text-sm mt-2">{Math.round(next.pct)}% — ${Number(next.current_amount).toFixed(2)} of ${Number(next.target_amount).toFixed(2)}</div>
                      </div>
                    );
                  })()
                )}
              </div>
            </div>
          </div>

          {/* Visual insights */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white rounded shadow p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="font-semibold">Income vs Expense (6 months)</div>
                <div className="text-xs text-gray-500">Trend</div>
              </div>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={monthlySeries}>
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="income" stroke="#34d399" strokeWidth={3} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="expense" stroke="#f87171" strokeWidth={3} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white rounded shadow p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="font-semibold">Expense distribution</div>
                <div className="text-xs text-gray-500">By category</div>
              </div>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={expenseByCategory} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90} paddingAngle={4}>
                      {expenseByCategory.map((_, i) => (
                        <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>

        {/* Logout confirmation modal */}
        {showLogoutConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="bg-white rounded-lg p-6 w-full max-w-sm">
              <h3 className="text-lg font-semibold mb-2">Confirm logout</h3>
              <p className="text-sm text-gray-600">Are you sure you want to logout? This will clear local session data.</p>
              <div className="flex justify-end gap-2 mt-4">
                <button onClick={() => setShowLogoutConfirm(false)} className="px-3 py-2 border rounded">Cancel</button>
                <button onClick={() => { setShowLogoutConfirm(false); doLogout(); }} className="px-3 py-2 bg-rose-600 text-white rounded">Logout</button>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}