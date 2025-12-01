if (typeof window !== "undefined" && !("global" in window)) {
  window.global = window;
}
import "./legacy.js";
import "./components/editor/index.js";
import "./main.js";
import "./teaching/index.js";
import "./supervising/index.js";
