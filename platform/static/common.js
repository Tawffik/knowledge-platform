// Shared helpers for the Nx01 Platform frontend (thin client of the REST API).
async function api(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(path + " -> " + r.status);
  return r.json();
}
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}
function money(n) {
  return n == null ? "—" : "$" + Number(n).toLocaleString("en-US");
}
function nav(active) {
  const items = [
    ["/", "الرئيسية Home"],
    ["/ui/projects", "المشاريع Projects"],
    ["/vault", "الخزنة Vault"],
    ["/ui/ledger", "سجل المعمل Lab Ledger"],
    ["/docs", "API Docs"],
  ];
  document.getElementById("nav").innerHTML =
    `<span class="logo">Nx01<b>_</b> Zero Track Sec</span>` +
    items.map(([href, lbl]) =>
      `<a class="item ${href === active ? "active" : ""}" href="${href}">${lbl}</a>`
    ).join("");
}
