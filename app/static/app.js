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
    var errorBox = document.querySelector("[data-scan-error]");
    var maxBytes = parseInt(form.getAttribute("data-max-bytes"), 10) || 0;
    var canSplit = typeof DataTransfer === "function" && list && template;
    if (canSplit) {
      try {
        new DataTransfer().items.add(new File([""], "probe.jpg"));
      } catch (error) {
        canSplit = false;
      }
    }

    function message(name, values) {
      var text = form.getAttribute("data-msg-" + name) || "";
      Object.keys(values || {}).forEach(function (key) {
        text = text.replace("{" + key + "}", values[key]);
      });
      return text;
    }

    // Problems are said above the form; the chosen photos stay where they are.
    function showError(text) {
      if (!errorBox) return;
      errorBox.textContent = text;
      errorBox.hidden = !text;
      if (text) errorBox.focus();
    }

    function tooBig(file) {
      return maxBytes > 0 && file.size > maxBytes;
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
        // Keep the keyboard where it was: the next photo's remove button, else the previous, else a picker.
        var neighbour = item.nextElementSibling || item.previousElementSibling;
        URL.revokeObjectURL(url);
        item.remove();
        refresh();
        var target = neighbour ? neighbour.querySelector(".shot-remove") : null;
        if (!target) {
          target = Array.prototype.filter.call(pickers, function (input) {
            return !input.disabled;
          })[0];
        }
        if (target) target.focus();
      });
      list.appendChild(item);
    }

    pickers.forEach(function (input) {
      input.addEventListener("change", function () {
        var problem = "";
        if (canSplit && input.files) {
          var files = Array.prototype.slice.call(input.files);
          var big = files.filter(tooBig);
          if (big.length) problem = message("big", { name: big[0].name });
          files = files.filter(function (file) {
            return !tooBig(file);
          });
          var room = Math.max(max - list.children.length, 0);
          files.slice(0, room).forEach(addShot);
          var dropped = files.length - room;
          if (dropped > 0 && !problem) {
            problem = dropped === 1 ? message("dropped-one") : message("dropped", { n: String(dropped) });
          }
          input.value = "";
        }
        showError(problem);
        refresh();
      });
    });

    // Send the photos without leaving the page, so a failed scan keeps them for another try.
    form.addEventListener("submit", function (event) {
      if (form.getAttribute("aria-busy") === "true") {
        event.preventDefault();
        event.stopImmediatePropagation();
        return;
      }
      if (count() === 0) {
        event.preventDefault();
        event.stopImmediatePropagation();
        showError(message("none"));
        return;
      }
      var big = [];
      pickers.forEach(function (input) {
        Array.prototype.forEach.call(input.files || [], function (file) {
          if (tooBig(file)) big.push(file);
        });
      });
      if (big.length) {
        event.preventDefault();
        event.stopImmediatePropagation();
        showError(message("big", { name: big[0].name }));
        return;
      }
      if (typeof window.fetch !== "function" || typeof window.FormData !== "function") return;
      event.preventDefault();
      event.stopImmediatePropagation();
      var data = new FormData(form);
      showError("");
      setBusy(form, true);
      window
        .fetch(form.action, { method: "POST", body: data, credentials: "same-origin" })
        .then(function (response) {
          return response.text().then(function (html) {
            return { ok: response.ok, html: html };
          });
        })
        .then(function (result) {
          if (result.ok) {
            // The review page: show it in place of this one.
            document.open();
            document.write(result.html);
            document.close();
            return;
          }
          var page = new DOMParser().parseFromString(result.html, "text/html");
          var notice = page.querySelector("[data-scan-error], .notice-error");
          setBusy(form, false);
          refresh();
          showError(notice && notice.textContent.trim() ? notice.textContent.trim() : message("offline"));
        })
        .catch(function () {
          setBusy(form, false);
          refresh();
          showError(message("offline"));
        });
    });
  });

  // Review list: Enter moves to the next field instead of saving the whole list part-way through.
  document.querySelectorAll(".review-form").forEach(function (form) {
    // A row's checkbox is named after the ingredient; keep that name in step with edits.
    form.addEventListener("input", function (event) {
      var target = event.target;
      if (!target.classList.contains("review-name")) return;
      var check = target.parentElement.querySelector(".check[data-label]");
      if (check) check.setAttribute("aria-label", check.getAttribute("data-label").replace("{name}", target.value.trim()));
    });
    form.addEventListener("keydown", function (event) {
      var target = event.target;
      if (event.key !== "Enter" || target.tagName !== "INPUT" || target.type === "checkbox") return;
      event.preventDefault();
      var fields = Array.prototype.slice.call(form.querySelectorAll("input:not([type=hidden]):not([type=checkbox])"));
      var next = fields[fields.indexOf(target) + 1];
      if (next) next.focus();
    });
  });

  // Destructive forms: the first tap arms the button, a second tap within four seconds sends it.
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    var button = form.querySelector("button");
    var label = button.textContent;
    var timer = 0;
    form.addEventListener("submit", function (event) {
      if (form.getAttribute("data-armed") === "true") return;
      event.preventDefault();
      form.setAttribute("data-armed", "true");
      button.textContent = form.getAttribute("data-confirm");
      timer = window.setTimeout(function () {
        form.removeAttribute("data-armed");
        button.textContent = label;
      }, 4000);
    });
    form.addEventListener("focusout", function () {
      window.clearTimeout(timer);
      form.removeAttribute("data-armed");
      button.textContent = label;
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
    if (panel) {
      panel.hidden = !busy;
      if (busy) {
        // A live region that was display:none is not announced; refill it once it is in the page.
        var message = panel.textContent;
        panel.textContent = "";
        window.setTimeout(function () {
          panel.textContent = message;
        }, 100);
      }
    }
    form.querySelectorAll("button, input[type=file]").forEach(function (control) {
      control.disabled = busy;
    });
    // Buttons elsewhere on the page that submit this form say so themselves while it works.
    if (form.id) {
      document.querySelectorAll('button[form="' + form.id + '"]').forEach(function (control) {
        var busyText = control.getAttribute("data-busy-text");
        if (busyText && busy) {
          control.setAttribute("data-label", control.textContent);
          control.textContent = busyText;
        } else if (control.hasAttribute("data-label")) {
          control.textContent = control.getAttribute("data-label");
        }
        control.disabled = busy;
      });
    }
    // One slow request at a time: the other waiting forms on the page are held while this one works.
    document.querySelectorAll("form[data-busy]").forEach(function (other) {
      if (other === form) return;
      other.querySelectorAll("button").forEach(function (control) {
        control.disabled = busy;
      });
      if (other.id) {
        document.querySelectorAll('button[form="' + other.id + '"]').forEach(function (control) {
          control.disabled = busy;
        });
      }
    });
  }

  document.querySelectorAll("form[data-busy]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (document.querySelector("form[aria-busy=true]")) {
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
