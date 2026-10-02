const $ = id => document.getElementById(id);
const money = n => "₹" + Number(n || 0).toLocaleString("en-IN", {maximumFractionDigits: 2});
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
$("month").value = new Date().toISOString().slice(0, 7);
$("date").value = new Date().toISOString().slice(0, 10);

async function api(url, opt) {
  const r = await fetch(url, opt);
  if (!r.ok) { alert("Request failed: " + r.status); throw new Error(r.status); }
  return r.json();
}
async function load() {
  const m = $("month").value;
  const [rep, txs] = await Promise.all([api("/api/report/" + m), api("/api/transactions?month=" + m)]);
  $("inc").textContent = money(rep.income);
  $("exp").textContent = money(rep.expense);
  $("sav").textContent = money(rep.savings);
  $("cats").innerHTML = rep.categories.map(c => {
    const base = c.monthly_limit || rep.expense || 1;
    const pct = Math.min(100, c.spent / base * 100);
    const lim = c.monthly_limit ? " / " + money(c.monthly_limit) + (c.over_budget ? " (OVER BUDGET)" : "") : "";
    return `<div>${esc(c.category)}: ${money(c.spent)}${lim}</div><div class="bar"><div class="${c.over_budget ? "over" : ""}" style="width:${pct}%"></div></div>`;
  }).join("") || "<p>No expenses yet.</p>";
  $("tbody").innerHTML = txs.map(t => `<tr><td>${t.tx_date}</td><td class="${t.kind}">${t.kind}</td><td>${esc(t.category)}</td><td>${esc(t.note)}</td><td>${money(t.amount)}</td><td><button class="del" data-id="${t.id}">Delete</button></td></tr>`).join("");
}
$("add").onclick = async () => {
  if (!$("cat").value.trim() || !(Number($("amt").value) > 0)) return alert("Enter category and a positive amount");
  await api("/api/transactions", {method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({kind: $("kind").value, category: $("cat").value, amount: Number($("amt").value), note: $("note").value, tx_date: $("date").value})});
  $("cat").value = $("amt").value = $("note").value = ""; load();
};
$("setb").onclick = async () => {
  if (!$("bcat").value.trim() || !(Number($("blim").value) > 0)) return alert("Enter category and limit");
  await api("/api/budgets", {method: "PUT", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({category: $("bcat").value, monthly_limit: Number($("blim").value)})});
  load();
};
$("tbody").onclick = async e => {
  if (e.target.dataset.id) { await api("/api/transactions/" + e.target.dataset.id, {method: "DELETE"}); load(); }
};
$("month").onchange = load;
load();
