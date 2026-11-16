/* Small progressive enhancements. Every page works without this file. */
(function () {
  "use strict";

  // Scan: say how many photos were chosen.
  document.querySelectorAll("input[type=file][data-count-into]").forEach(function (input) {
    var out = document.getElementById(input.getAttribute("data-count-into"));
    if (!out) return;
    input.addEventListener("change", function () {
      var n = input.files ? input.files.length : 0;
      if (n === 0) {
        out.textContent = "";
      } else if (n === 1) {
        out.textContent = out.getAttribute("data-one");
      } else {
        out.textContent = out.getAttribute("data-many").replace("{n}", String(n));
      }
    });
  });

  // Slow AI requests: show the waiting message and block a second tap.
  function setBusy(form, busy) {
    if (busy) {
      form.setAttribute("aria-busy", "true");
    } else {
      form.removeAttribute("aria-busy");
    }
    var panel = form.querySelector("[data-busy-panel]");
    if (panel) panel.hidden = !busy;
    form.querySelectorAll("button").forEach(function (button) {
      button.disabled = busy;
    });
  }

  document.querySelectorAll("form[data-busy]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (form.getAttribute("aria-busy") === "true") {
        event.preventDefault();
        return;
      }
      // Wait a tick so the browser first collects the form, including the pressed button.
      window.setTimeout(function () {
        setBusy(form, true);
      }, 0);
    });
  });

  // Coming back with the browser's Back button: clear any waiting state.
  window.addEventListener("pageshow", function (event) {
    if (!event.persisted) return;
    document.querySelectorAll("form[aria-busy=true]").forEach(function (form) {
      setBusy(form, false);
    });
  });
})();
