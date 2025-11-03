// Prevent zoom and layout shifts during reload
(function() {
  'use strict';
  
  function initLoadingState() {
    if (document.body) {
      document.body.classList.add('loading');
      
      // Remove loading class after page is fully loaded
      window.addEventListener('load', function() {
        setTimeout(function() {
          if (document.body) {
            document.body.classList.remove('loading');
          }
        }, 100);
      });
    } else {
      // Wait for body to be available
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLoadingState);
      } else {
        setTimeout(initLoadingState, 10);
      }
    }
  }
  
  initLoadingState();
  
  // Prevent zoom on double-tap (mobile) - but allow clicks on buttons/interactive elements
  let lastTouchEnd = 0;
  document.addEventListener('touchend', function(event) {
    const target = event.target;
    // Never prevent on buttons, links, or any interactive element
    if (target && (
      target.tagName === 'BUTTON' || 
      target.tagName === 'A' || 
      target.tagName === 'INPUT' ||
      target.tagName === 'SELECT' ||
      target.getAttribute('role') === 'button' ||
      target.closest('button') || 
      target.closest('a') ||
      target.closest('[role="button"]')
    )) {
      return; // Allow the event to proceed normally for interactive elements
    }
    
    const now = Date.now();
    if (now - lastTouchEnd <= 300) {
      event.preventDefault();
    }
    lastTouchEnd = now;
  }, { passive: false });
  
  // Maintain viewport scale during reload
  if ('scrollBehavior' in document.documentElement.style) {
    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport) {
      const savedScale = sessionStorage.getItem('viewport-scale');
      if (savedScale) {
        viewport.setAttribute('content', viewport.getAttribute('content').replace(/initial-scale=[^,]+/, 'initial-scale=' + savedScale));
      }
    }
  }
})();

// Auto-refresh every 60s (adjust if you like)
setTimeout(() => {
  // Save current viewport scale before reload
  const viewport = document.querySelector('meta[name="viewport"]');
  if (viewport) {
    const content = viewport.getAttribute('content');
    const scaleMatch = content.match(/initial-scale=([^,]+)/);
    if (scaleMatch) {
      sessionStorage.setItem('viewport-scale', scaleMatch[1]);
    }
  }
  
  // Use location.replace instead of reload to avoid zoom issues
  location.replace(location.href);
}, 60000);

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

// Style toggle functionality
function initStyleToggle() {
  const mainStylesheet = document.getElementById('main-stylesheet');
  const experimentalStylesheet = document.getElementById('experimental-stylesheet');
  const styleToggle = document.getElementById('styleToggle');
  const toggleSwitch = document.querySelector('.toggle-switch');
  
  if (!mainStylesheet || !experimentalStylesheet) {
    console.error('Stylesheets not found');
    return;
  }
  
  // Initialize styles based on preference
  function setStyle(useExperimental) {
    try {
      if (useExperimental) {
        mainStylesheet.disabled = true;
        experimentalStylesheet.disabled = false;
        experimentalStylesheet.removeAttribute('disabled');
        if (toggleSwitch) toggleSwitch.classList.add('active');
      } else {
        mainStylesheet.disabled = false;
        experimentalStylesheet.disabled = true;
        experimentalStylesheet.setAttribute('disabled', 'disabled');
        if (toggleSwitch) toggleSwitch.classList.remove('active');
      }
      localStorage.setItem('useExperimentalStyle', useExperimental);
    } catch (error) {
      console.error('Error setting style:', error);
    }
  }
  
  // Check localStorage for saved preference
  const useExperimental = localStorage.getItem('useExperimentalStyle') === 'true';
  
  // Set initial style
  setStyle(useExperimental);
  
  // Toggle on button click
  if (styleToggle) {
    styleToggle.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      const currentlyExperimental = !experimentalStylesheet.disabled;
      setStyle(!currentlyExperimental);
      return false;
    }, false);
    
    // Also handle touch events for mobile
    styleToggle.addEventListener('touchend', function(e) {
      e.preventDefault();
      e.stopPropagation();
      const currentlyExperimental = !experimentalStylesheet.disabled;
      setStyle(!currentlyExperimental);
      return false;
    }, false);
  }
}

// Run initialization after everything is loaded
function runStyleToggle() {
  // Wait a bit to ensure DOM is fully ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(initStyleToggle, 50);
    });
  } else {
    setTimeout(initStyleToggle, 50);
  }
}

runStyleToggle();