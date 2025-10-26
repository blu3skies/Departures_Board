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

// Handle weather modal functionality
document.addEventListener("click", function (e) {
  const modal = document.getElementById("weatherModal");
  const moreDetailsBtn = document.querySelector(".weather-more-details-btn");
  const closeBtn = document.querySelector(".weather-modal-close");
  const tabBtns = document.querySelectorAll(".weather-tab-btn");

  // Open modal when "More Details" button is clicked
  if (moreDetailsBtn && moreDetailsBtn.contains(e.target)) {
    modal.classList.add("active");
  }

  // Close modal when close button is clicked
  if (closeBtn && closeBtn.contains(e.target)) {
    modal.classList.remove("active");
  }

  // Close modal when clicking outside the modal content
  if (modal && modal.contains(e.target) && !modal.querySelector(".weather-modal-content").contains(e.target)) {
    modal.classList.remove("active");
  }

  // Handle tab switching
  tabBtns.forEach(btn => {
    if (btn.contains(e.target)) {
      const tabName = btn.getAttribute("data-tab");
      
      // Remove active class from all tabs and panels
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".weather-tab-panel").forEach(panel => {
        panel.classList.remove("active");
      });
      
      // Add active class to clicked tab and corresponding panel
      btn.classList.add("active");
      document.getElementById(tabName + "-tab").classList.add("active");
    }
  });
});

// Close modal with Escape key
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    const modal = document.getElementById("weatherModal");
    if (modal && modal.classList.contains("active")) {
      modal.classList.remove("active");
    }
  }
});