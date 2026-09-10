/* ============================================================
   Shared UI helpers — toast notes, button loading states.
   Included on every page before the page-specific script.
   ============================================================ */

function showToast(message) {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 4000);
}

const COMPASS_SVG = `
  <svg class="spinner" viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="9.5" stroke="currentColor" stroke-width="1.6"/>
    <path d="M12 12 L16 7 L13 13 L8 17 Z" fill="currentColor"/>
  </svg>`;

function setLoading(button, isLoading, loadingText, normalText) {
  if (isLoading) {
    button.dataset.originalHtml = button.innerHTML;
    button.innerHTML = `${COMPASS_SVG} ${loadingText || "Working..."}`;
    button.disabled = true;
  } else {
    button.innerHTML = button.dataset.originalHtml || normalText || button.innerHTML;
    button.disabled = false;
  }
}
