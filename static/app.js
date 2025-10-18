// Auto-refresh every 60s (adjust if you like)
setTimeout(() => location.reload(), 60000);

// Handle tube "Show details" popups
document.addEventListener("click", function (e) {
  const buttons = document.querySelectorAll(".reason-toggle");
  buttons.forEach(btn => {
    const popup = btn.nextElementSibling;
    if (!popup) return;

    if (btn.contains(e.target)) {
      // Toggle the clicked popup
      const isActive = popup.classList.toggle("active");
      btn.textContent = isActive ? "Hide details" : "Show details";
    } else if (!popup.contains(e.target)) {
      // Close other popups
      popup.classList.remove("active");
      btn.textContent = "Show details";
    }
  });
});