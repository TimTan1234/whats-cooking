/* Small progressive enhancements. Every page works without this file. */
(function () {
  "use strict";

  // Scan: every photo, from the camera or the gallery, becomes its own entry that can be
  // removed, so several camera shots add up instead of replacing each other.
  document.querySelectorAll("form[data-photos]").forEach(function (form) {
    var max = parseInt(form.getAttribute("data-max"), 10) || 4;
    var pickers = form.querySelectorAll(".picker input[type=file]");
    var list = form.querySelector(".shots");
    var template = document.getElementById("shot-template");
    var status = form.querySelector(".chosen");
    var canSplit = typeof DataTransfer === "function" && list && template;
    if (canSplit) {
      try {
        new DataTransfer().items.add(new File([""], "probe.jpg"));
      } catch (error) {
        canSplit = false;
      }
    }

    function count() {
      var n = list ? list.children.length : 0;
      pickers.forEach(function (input) {
        n += input.files ? input.files.length : 0;
      });
      return n;
    }

    function refresh() {
      var n = count();
      var text = "";
      if (n === 1) {
        text = status.getAttribute("data-one");
      } else if (n > 1) {
        text = status.getAttribute("data-many").replace("{n}", String(n));
      }
      if (n >= max) text = status.getAttribute("data-full").replace("{n}", String(n));
      status.textContent = text;
      if (list) {
        list.hidden = list.children.length === 0;
        Array.prototype.forEach.call(list.children, function (item, index) {
          var button = item.querySelector(".shot-remove");
          button.setAttribute("aria-label", button.getAttribute("data-label").replace("{n}", String(index + 1)));
        });
      }
      if (canSplit) {
        pickers.forEach(function (input) {
          input.disabled = n >= max;
        });
      }
    }

    function addShot(file) {
      var item = template.content.firstElementChild.cloneNode(true);
      var holder = document.createElement("input");
      var transfer = new DataTransfer();
      transfer.items.add(file);
      holder.type = "file";
      holder.name = "photos";
      holder.hidden = true;
      holder.files = transfer.files;
      var url = URL.createObjectURL(file);
      var image = item.querySelector("img");
      image.src = url;
      item.appendChild(holder);
      item.querySelector(".shot-remove").addEventListener("click", function () {
        URL.revokeObjectURL(url);
        item.remove();
        refresh();
      });
      list.appendChild(item);
    }

    pickers.forEach(function (input) {
      input.addEventListener("change", function () {
        if (canSplit && input.files) {
          var room = max - list.children.length;
          Array.prototype.slice.call(input.files, 0, Math.max(room, 0)).forEach(addShot);
          input.value = "";
        }
        refresh();
      });
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
