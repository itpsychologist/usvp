// Інтерактивність сайту УСВП без залежностей і без inline-скриптів (сумісно з суворою CSP).
//
// 1. Розкривні елементи (патерн disclosure): <button data-disclosure aria-controls="id" aria-expanded="false">
//    перемикає атрибут data-open у панелі #id (панель позначена data-disclosure-panel; CSS ховає її лише
//    коли JS працює, тож без JS весь вміст доступний). Esc закриває спливну панель і повертає фокус.
//    data-disclosure-autoclose — закривати при кліку поза панеллю і при переході фокуса з неї.
//    data-modal на панелі — модальний діалог: решта сторінки отримує inert, фокус лишається всередині.
// 2. Панель доступності: <button data-a11y="font|contrast|underline" data-value="..." aria-pressed>.
(function () {
  "use strict";

  var STORAGE_KEY = "usvp-a11y";
  var inerted = [];

  function targetOf(button) {
    return document.getElementById(button.getAttribute("aria-controls"));
  }

  function controlsOf(target) {
    return document.querySelectorAll('[data-disclosure][aria-controls="' + target.id + '"]');
  }

  function isOpen(target) {
    return target.hasAttribute("data-open");
  }

  // Робить усе поза модальною панеллю недоступним для фокуса й скрінрідерів
  function setModal(target, on) {
    inerted.forEach(function (el) {
      el.inert = false;
    });
    inerted = [];
    if (!on) return;
    for (var node = target; node && node !== document.body; node = node.parentElement) {
      Array.prototype.forEach.call(node.parentElement.children, function (sibling) {
        if (sibling !== node && !sibling.inert && sibling.tagName !== "SCRIPT") {
          sibling.inert = true;
          inerted.push(sibling);
        }
      });
    }
  }

  function setOpen(button, open, moveFocus) {
    var target = targetOf(button);
    if (!target) return;
    // Панель може мати кілька кнопок (наприклад, «Меню» у шапці й «Закрити» в самій панелі)
    controlsOf(target).forEach(function (control) {
      control.setAttribute("aria-expanded", open ? "true" : "false");
    });
    var hadFocus = target.contains(document.activeElement);
    target.toggleAttribute("data-open", open);
    if (target.hasAttribute("data-modal")) {
      setModal(target, open);
      document.documentElement.classList.toggle("overflow-hidden", open);
    }
    if (!moveFocus) return;
    if (open && target.hasAttribute("data-modal")) {
      var first = target.querySelector("a[href], button, input, select, textarea");
      if (first) first.focus();
    } else if (!open && hadFocus) {
      // Повертаємо фокус на кнопку поза панеллю, що її відкрила
      Array.prototype.some.call(controlsOf(target), function (control) {
        if (target.contains(control)) return false;
        control.focus();
        return true;
      });
    }
  }

  function openButtons() {
    return document.querySelectorAll('[data-disclosure][aria-expanded="true"]');
  }

  function closeOthers(except) {
    openButtons().forEach(function (button) {
      if (button === except || !button.hasAttribute("data-disclosure-autoclose")) return;
      var target = targetOf(button);
      // Не закриваємо батьківську панель (наприклад, мобільне меню з підменю)
      if (target && target.contains(except)) return;
      setOpen(button, false);
    });
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-disclosure]");
    if (button) {
      var target = targetOf(button);
      closeOthers(button);
      setOpen(button, !(target && isOpen(target)), true);
      return;
    }
    openButtons().forEach(function (btn) {
      var target = targetOf(btn);
      if (btn.hasAttribute("data-disclosure-autoclose") && target && !target.contains(event.target)) {
        setOpen(btn, false);
      }
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    // Esc закриває лише спливні панелі (меню, панель доступності, мобільне меню), не вбудовані підменю
    var buttons = Array.prototype.filter.call(openButtons(), function (button) {
      var target = targetOf(button);
      if (!target || !isOpen(target)) return false;
      if (target.hasAttribute("data-modal")) return !target.contains(button);
      return button.hasAttribute("data-disclosure-autoclose") && button.getClientRects().length > 0;
    });
    if (!buttons.length) return;
    var button = buttons[buttons.length - 1];
    var target = targetOf(button);
    var hadFocus = target.contains(document.activeElement);
    setOpen(button, false, true);
    if (!hadFocus) button.focus();
  });

  document.addEventListener("focusout", function (event) {
    var next = event.relatedTarget;
    if (!next) return;
    openButtons().forEach(function (button) {
      if (!button.hasAttribute("data-disclosure-autoclose")) return;
      var target = targetOf(button);
      if (target && target.contains(event.target) && !target.contains(next) && next !== button) {
        setOpen(button, false);
      }
    });
  });

  // Роль діалогу отримують лише панелі, що справді стають модальними (тобто коли працює JS)
  document.querySelectorAll("[data-modal]").forEach(function (panel) {
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-modal", "true");
    panel.setAttribute("aria-labelledby", panel.getAttribute("data-modal-label"));
  });

  // Мобільне меню не має лишатися відкритим (і блокувати прокрутку) після розширення вікна
  var desktop = window.matchMedia("(min-width: 64rem)");
  desktop.addEventListener("change", function (event) {
    if (!event.matches) return;
    document.querySelectorAll("[data-modal][data-open]").forEach(function (panel) {
      setOpen(controlsOf(panel)[0], false);
    });
  });

  // Панель доступності
  function loadPrefs() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    } catch (e) {
      return {};
    }
  }

  function savePrefs(prefs) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    } catch (e) {
      // Без збереження налаштування діють до перезавантаження сторінки
    }
  }

  function syncA11yButtons(prefs) {
    document.querySelectorAll("[data-a11y]").forEach(function (button) {
      var key = button.getAttribute("data-a11y");
      if (key === "reset") return;
      var value = button.getAttribute("data-value") || "";
      var current = prefs[key] || "";
      button.setAttribute("aria-pressed", current === value ? "true" : "false");
    });
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-a11y]");
    if (!button) return;
    var prefs = loadPrefs();
    var key = button.getAttribute("data-a11y");
    var value = button.getAttribute("data-value") || "";
    var root = document.documentElement;
    if (key === "reset") {
      prefs = {};
      ["font", "contrast", "underline"].forEach(function (k) {
        root.removeAttribute("data-" + k);
      });
    } else if (value) {
      prefs[key] = value;
      root.setAttribute("data-" + key, value);
    } else {
      delete prefs[key];
      root.removeAttribute("data-" + key);
    }
    savePrefs(prefs);
    syncA11yButtons(prefs);
  });

  syncA11yButtons(loadPrefs());
})();
