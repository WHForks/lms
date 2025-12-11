import "./legacy.js";
import "bootstrap-sass";
import $ from "jquery";
import "jgrowl/jquery.jgrowl.js";
import "bootstrap-select/js/bootstrap-select";
import "jasny-bootstrap/js/fileinput";

import "mathjax_config";
import UberEditor from "components/editor";
import {
  csrfSafeMethod,
  getCSRFToken,
  getSections,
  showComponentError,
  loadReactApplications,
  createNotification,
} from "./utils";
import hljs from "highlight.js";
import * as forms from "components/forms";
import { launch as launchLazyload } from "components/lazyload";
import { launch as launchCourseDetails } from "courses/courseDetails";
import { launch as launchCourseOfferings } from "courses/courseOfferings";
import { launch as launchProfile } from "users/profile";
import { launch as launchSolution } from "learning/solution";

const CSC = window.__CSC__;

const THEME_STORAGE_KEY = "csc-theme";

function applyStoredTheme() {
  try {
    const stored =
      window.localStorage && window.localStorage.getItem(THEME_STORAGE_KEY);
    const root = document.documentElement;
    if (stored === "dark") {
      root.setAttribute("data-theme", "dark");
    } else if (stored === "light") {
      root.removeAttribute("data-theme");
    } else {
      const prefersDark =
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches;
      if (prefersDark) {
        root.setAttribute("data-theme", "dark");
      } else {
        root.removeAttribute("data-theme");
      }
    }
  } catch (e) {
    // ignore storage errors
  }
}

function handleSystemThemeChange(e) {
  try {
    const stored =
      window.localStorage && window.localStorage.getItem(THEME_STORAGE_KEY);
    // Only sync with system if user hasn't manually set a theme
    if (!stored) {
      const root = document.documentElement;
      if (e.matches) {
        root.setAttribute("data-theme", "dark");
      } else {
        root.removeAttribute("data-theme");
      }
    }
  } catch (err) {
    // ignore storage errors
  }
}

function toggleTheme() {
  const root = document.documentElement;
  const isDark = root.getAttribute("data-theme") === "dark";
  const next = isDark ? "light" : "dark";

  if (next === "dark") {
    root.setAttribute("data-theme", "dark");
  } else {
    root.removeAttribute("data-theme");
  }

  try {
    if (window.localStorage) {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    }
  } catch (e) {
    // ignore storage errors
  }
}

$(document).ready(function () {
  applyStoredTheme();

  // Sync with system theme changes unless user has manually set a preference
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  if (media && media.addEventListener) {
    media.addEventListener("change", handleSystemThemeChange);
  } else if (media && media.addListener) {
    // Safari/older browsers
    media.addListener(handleSystemThemeChange);
  }

  configureCSRFAjax();
  displayNotifications();
  renderText();
  initUberEditors();
  initCollapsiblePanelGroups();
  setupFileInputs();

  let sections = getSections();
  if (sections.includes("datetimepickers")) {
    try {
      forms.initDatePickers();
      forms.initTimePickers();
    } catch (error) {
      showComponentError(error);
    }
  }
  if (sections.includes("selectpickers")) {
    try {
      forms.initSelectPickers();
    } catch (error) {
      showComponentError(error);
    }
  }
  if (sections.includes("lazy-img")) {
    try {
      launchLazyload();
    } catch (error) {
      showComponentError(error);
    }
  }
  // FIXME: combine into one peace `courses`?
  if (sections.includes("courseDetails")) {
    try {
      launchCourseDetails();
    } catch (error) {
      showComponentError(error);
    }
  }
  if (sections.includes("courseOfferings")) {
    try {
      launchCourseOfferings();
    } catch (error) {
      showComponentError(error);
    }
  }
  if (sections.includes("profile")) {
    try {
      launchProfile();
    } catch (error) {
      showComponentError(error);
    }
  }
  if (sections.includes("learning/solution")) {
    try {
      launchSolution();
    } catch (error) {
      showComponentError(error);
    }
  }

  const themeToggles = document.querySelectorAll(".js-theme-toggle");

  themeToggles.forEach((btn) => {
    btn.addEventListener("click", toggleTheme);
  });

  loadReactApplications();
});

function displayNotifications() {
  if (window.__CSC__.notifications !== undefined) {
    window.__CSC__.notifications.forEach((message) => {
      $.jGrowl(message.text, {
        position: "bottom-right",
        sticky: message.timeout !== 0,
        theme: message.type,
      });
    });
  }
}

function configureCSRFAjax() {
  // Append csrf token on ajax POST requests made with jQuery
  // FIXME: add support for allowed subdomains
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
      }
    },
  });
}

function renderText() {
  // highlight js and MathJax
  const $ubertexts = $("div.ubertext");
  // Note: MathJax and hljs loads for each iframe separately
  if ($ubertexts.length > 0) {
    UberEditor.preload(function () {
      // Configure highlight js
      hljs.configure({ tabReplace: "    " });
      // Render Latex and highlight code
      $ubertexts.each(function (i, target) {
        UberEditor.render(target);
      });
    });
  }
}

function initUberEditors() {
  // Replace textarea with EpicEditor
  const $ubereditors = $("textarea.ubereditor");
  UberEditor.cleanLocalStorage($ubereditors);
  $ubereditors.each(function (i, textarea) {
    const editor = UberEditor.init(textarea);
    CSC.config.uberEditors.push(editor);
  });
  if ($ubereditors.length > 0) {
    $('a[data-toggle="tab"]').on("shown.bs.tab", UberEditor.reflowOnTabToggle);
  }
}

function initCollapsiblePanelGroups() {
  $(".panel-group").on("click", ".panel-heading._arrowed", function (e) {
    // Replace js animation with css.
    e.preventDefault();
    const open = $(this).attr("aria-expanded") === "true";
    $(this).next().toggleClass("collapse").attr("aria-expanded", !open);
    $(this).attr("aria-expanded", !open);
  });
}

function setupFileInputs() {
  $(".jasny.fileinput")
    .on("clear.bs.fileinput", function (event) {
      $(event.target).find(".fileinput-clear-checkbox").val("on");
      $(event.target).find(".fileinput-filename").text("No file selected");
    })
    .on("change.bs.fileinput", function (event) {
      $(event.target).find(".fileinput-clear-checkbox").val("");
    })
    .on("reseted.bs.fileinput", function (event) {
      $(event.target).find(".fileinput-filename").text("No file selected");
      $(event.target).find(".fileinput-clear-checkbox").val("on");
    });
  const fileInputs = document.querySelectorAll(
    '.jasny.fileinput input[type="file"]',
  );
  const maxUploadSize = window.__CSC__.config.maxUploadSize;
  const maxUploadSizeStr = maxUploadSize / 1024 / 1024 + " MiB";
  fileInputs.forEach((fileInput) => {
    fileInput.addEventListener("change", (e) => {
      for (const file of e.target.files) {
        if (file.size > maxUploadSize) {
          createNotification(
            "Cannot upload files larger than " + maxUploadSizeStr,
            "error",
          );
          e.target.value = null;
        }
      }
    });
  });
}
