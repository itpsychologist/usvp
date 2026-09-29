// Застосовує збережені налаштування доступності до першого рендеру, щоб не було «блимання»,
// і позначає <html> класом js.
// Підключається синхронно в <head>; решта логіки панелі — у site.js.
(function () {
  // Клас js вмикає розкривні панелі; без нього (JS вимкнено) меню показуються розгорнутими
  document.documentElement.classList.add("js");
  try {
    var prefs = JSON.parse(localStorage.getItem("usvp-a11y") || "{}");
    var root = document.documentElement;
    ["font", "contrast", "underline"].forEach(function (key) {
      if (prefs[key]) root.setAttribute("data-" + key, prefs[key]);
    });
  } catch (e) {
    // localStorage недоступний (приватний режим тощо) — працюємо з типовими налаштуваннями
  }
})();
