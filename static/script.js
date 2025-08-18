function formatMoney(n) {
    return `$${n.toFixed(2)}`;
}

document.addEventListener("DOMContentLoaded", () => {
    const reviewBtn = document.getElementById("review");
    const form = document.getElementById("order-form");
    const summary = document.getElementById("summary");

    reviewBtn.addEventListener("click", () => {
        const fd = new FormData(form);
        const table = fd.get("table");
        if (!table) {
            alert("Please enter a table number.");
            return;
        }

        // Collect selected items (qty > 0)
        const items = [];
        for (const [key, val] of fd.entries()) {
            if (key.startsWith("qty_")) {
                const id = Number(key.split("_")[1]);
                const qty = Number(val || 0);
                if (qty > 0) {
                    // find matching item info from a data attribute rendered into DOM
                    const el = document.querySelector(`[data-item-id="${id}"]`);
                    const name = el?.dataset.name || `Item ${id}`;
                    const price = Number(el?.dataset.price || 0);
                    items.push({ id, name, price, qty, lineTotal: qty * price });
                }
            }
        }

        if (items.length === 0) {
            alert("Please choose at least one item.");
            return;
        }

        const subtotal = items.reduce((s, it) => s + it.lineTotal, 0);

        // Render a quick summary
        summary.classList.remove("hidden");
        summary.innerHTML = `
            <h3>Order Summary (Table ${table})</h3>
            <ul>
                ${items.map(it => `<li>${it.qty} × ${it.name} — ${formatMoney(it.lineTotal)}</li>`).join("")}
            </ul>
            <p><strong>Subtotal:</strong> ${formatMoney(subtotal)}</p>
            <p style="color:#6b7280;margin-top:6px;">(Next step: send to server & save)</p>
        `;
    });
});
