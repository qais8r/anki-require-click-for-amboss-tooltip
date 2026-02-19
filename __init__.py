from aqt import gui_hooks, mw

_AMBOSS_TRIGGER_PATCH_JS = r"""
(function () {
  var FORCE_TRIGGER = "click";
  var COMPAT_TRIGGER = "mouseenter click";
  var ROOT_SELECTOR = "#qa";
  var MARKER_SELECTOR = ".amboss-marker";

  function installOneByOneStopPropagationBypass() {
    if (window.__ambossStopPropagationBypassInstalled) {
      return;
    }

    var originalStopPropagation = Event.prototype.stopPropagation;
    Event.prototype.stopPropagation = function () {
      try {
        if (!this || this.type !== "click") {
          return originalStopPropagation.apply(this, arguments);
        }

        var target = this.target;
        var currentTarget = this.currentTarget;
        var marker = target && typeof target.closest === "function"
          ? target.closest(MARKER_SELECTOR)
          : null;

        var isOneByOneClozeHandler =
          currentTarget &&
          currentTarget.classList &&
          currentTarget.classList.contains("cloze") &&
          currentTarget.classList.contains("one-by-one");

        // Let marker clicks bubble past one-by-one cloze handler so delegated
        // AMBOSS click listeners can run on template-only runtimes.
        if (marker && isOneByOneClozeHandler) {
          return;
        }
      } catch (_error) {}

      return originalStopPropagation.apply(this, arguments);
    };

    window.__ambossStopPropagationBypassInstalled = true;
  }

  function setTriggerOnOptions(options, triggerValue) {
    if (!options || typeof options !== "object") {
      return false;
    }
    options.trigger = triggerValue || FORCE_TRIGGER;
    return true;
  }

  function patchInstance(instance) {
    if (!instance || typeof instance !== "object") {
      return false;
    }

    try {
      if (typeof instance.setProps === "function") {
        instance.setProps({ trigger: FORCE_TRIGGER });
        return true;
      }
      if (typeof instance.set === "function") {
        instance.set({ trigger: FORCE_TRIGGER });
        return true;
      }
      if (instance.props && typeof instance.props === "object") {
        instance.props.trigger = FORCE_TRIGGER;
        return true;
      }
    } catch (_error) {}

    return false;
  }

  function patchElementTippy(element) {
    if (!element || typeof element !== "object") {
      return false;
    }
    return patchInstance(element._tippy);
  }

  function closestMarker(target) {
    if (!target) {
      return null;
    }

    var node = target.nodeType === 3 ? target.parentElement : target;
    if (node && typeof node.closest === "function") {
      return node.closest(MARKER_SELECTOR);
    }

    while (node && node !== document) {
      if (
        node.nodeType === 1 &&
        typeof node.matches === "function" &&
        node.matches(MARKER_SELECTOR)
      ) {
        return node;
      }
      node = node.parentNode;
    }

    return null;
  }

  function isInsideTooltip(target) {
    if (!target) {
      return false;
    }

    var node = target.nodeType === 3 ? target.parentElement : target;
    if (!node || typeof node.closest !== "function") {
      return false;
    }

    return Boolean(node.closest(".tippy-popper, .tippy-box, [data-tippy-root]"));
  }

  function resolveManagers() {
    var managers = [];

    var controller = window.ambossController;
    if (
      controller &&
      typeof controller === "object" &&
      controller.ambossTooltips &&
      typeof controller.ambossTooltips === "object"
    ) {
      managers.push(controller.ambossTooltips);
    }

    var addon = window.ambossAddon && window.ambossAddon.tooltip;
    if (addon && (typeof addon === "object" || typeof addon === "function")) {
      managers.push(addon);
      if (addon.tooltips) {
        managers.push(addon.tooltips);
      }
      if (addon.default) {
        managers.push(addon.default);
      }
    }

    var unique = [];
    for (var i = 0; i < managers.length; i += 1) {
      if (managers[i] && unique.indexOf(managers[i]) === -1) {
        unique.push(managers[i]);
      }
    }

    return unique;
  }

  function patchManager(manager) {
    if (!manager || (typeof manager !== "object" && typeof manager !== "function")) {
      return false;
    }

    var patched = false;

    var isCompatManager = Boolean(
      manager &&
        typeof manager.showTooltipOnElement !== "function" &&
        typeof manager.hideAll === "function"
    );

    var forceTrigger = isCompatManager ? COMPAT_TRIGGER : FORCE_TRIGGER;

    if (setTriggerOnOptions(manager.tippyOptions, forceTrigger)) {
      patched = true;
    }
    if (setTriggerOnOptions(manager.delegateOptions, forceTrigger)) {
      patched = true;
    }

    if (Array.isArray(manager.instances)) {
      for (var i = 0; i < manager.instances.length; i += 1) {
        if (patchInstance(manager.instances[i])) {
          patched = true;
        }
      }
    }

    if (!manager.__forceClickInitPatched && typeof manager.initialize === "function") {
      var originalInitialize = manager.initialize;
      manager.initialize = function () {
        var initTrigger = FORCE_TRIGGER;
        if (
          this &&
          typeof this.showTooltipOnElement !== "function" &&
          typeof this.hideAll === "function"
        ) {
          initTrigger = COMPAT_TRIGGER;
        }
        setTriggerOnOptions(this && this.tippyOptions, initTrigger);
        setTriggerOnOptions(this && this.delegateOptions, initTrigger);
        var value = originalInitialize.apply(this, arguments);
        var selector = (this && this.selector) || ROOT_SELECTOR;
        var root = typeof selector === "string" ? document.querySelector(selector) : null;
        if (root) {
          patchElementTippy(root);
        }
        return value;
      };
      manager.__forceClickInitPatched = true;
      patched = true;
    }

    if (
      !manager.__forceClickCreatePatched &&
      typeof manager._createTippyOnElement === "function"
    ) {
      var originalCreate = manager._createTippyOnElement;
      manager._createTippyOnElement = function (element) {
        var createTrigger =
          this &&
          typeof this.showTooltipOnElement !== "function" &&
          typeof this.hideAll === "function"
            ? COMPAT_TRIGGER
            : FORCE_TRIGGER;
        setTriggerOnOptions(this && this.tippyOptions, createTrigger);
        var instance = originalCreate.call(this, element);
        patchInstance(instance);
        patchElementTippy(element);
        return instance;
      };
      manager.__forceClickCreatePatched = true;
      patched = true;
    }

    return patched;
  }

  function patchManagers() {
    var managers = resolveManagers();
    var patched = false;
    for (var i = 0; i < managers.length; i += 1) {
      if (patchManager(managers[i])) {
        patched = true;
      }
    }
    return patched;
  }

  function patchExistingElements() {
    var patched = false;
    var root = document.querySelector(ROOT_SELECTOR);
    if (root && patchElementTippy(root)) {
      patched = true;
    }

    var markers = document.querySelectorAll(MARKER_SELECTOR);
    for (var i = 0; i < markers.length; i += 1) {
      if (patchElementTippy(markers[i])) {
        patched = true;
      }
    }

    return patched;
  }

  function getOrCreateMarkerInstance(marker) {
    if (!marker) {
      return null;
    }

    if (marker._tippy) {
      patchInstance(marker._tippy);
      return marker._tippy;
    }

    var managers = resolveManagers();
    for (var i = 0; i < managers.length; i += 1) {
      var manager = managers[i];
      if (!manager || typeof manager._createTippyOnElement !== "function") {
        continue;
      }

      try {
        var created = manager._createTippyOnElement(marker);
        patchInstance(created);
        patchElementTippy(marker);
        if (marker._tippy) {
          return marker._tippy;
        }
        if (created) {
          return created;
        }
      } catch (_error) {}
    }

    return marker._tippy || null;
  }

  function showTooltipFromManagers(marker) {
    var managers = resolveManagers();

    for (var i = 0; i < managers.length; i += 1) {
      var manager = managers[i];
      if (!manager || typeof manager.showTooltipOnElement !== "function") {
        continue;
      }
      try {
        manager.showTooltipOnElement(marker);
        patchElementTippy(marker);
        if (
          marker._tippy &&
          marker._tippy.state &&
          marker._tippy.state.isVisible
        ) {
          return true;
        }
      } catch (_error) {}
    }

    return false;
  }

  function hideAllTooltips() {
    var hidden = false;

    try {
      if (window.tippy && typeof window.tippy.hideAll === "function") {
        window.tippy.hideAll({ duration: 0 });
        hidden = true;
      }
    } catch (_error) {}

    var managers = resolveManagers();
    for (var i = 0; i < managers.length; i += 1) {
      var manager = managers[i];
      if (!manager || typeof manager.hideAll !== "function") {
        continue;
      }
      try {
        manager.hideAll();
        hidden = true;
      } catch (_error) {}
    }

    try {
      var markers = document.querySelectorAll(MARKER_SELECTOR);
      for (var j = 0; j < markers.length; j += 1) {
        var instance = markers[j]._tippy;
        if (
          instance &&
          instance.state &&
          instance.state.isVisible &&
          typeof instance.hide === "function"
        ) {
          instance.hide();
          hidden = true;
        }
      }
    } catch (_error) {}

    return hidden;
  }

  function stopEvent(event) {
    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }
    if (typeof event.stopPropagation === "function") {
      event.stopPropagation();
    }
    if (typeof event.preventDefault === "function") {
      event.preventDefault();
    }
  }

  function syntheticOpenFromClick(marker) {
    if (!marker || typeof marker.dispatchEvent !== "function") {
      return false;
    }

    marker.__ambossSyntheticOpen = true;
    try {
      // Delegated tippy listeners are often bound to mouseover/mouseenter.
      marker.dispatchEvent(
        new MouseEvent("mouseover", {
          bubbles: true,
          cancelable: true,
          view: window,
        })
      );
      marker.dispatchEvent(
        new MouseEvent("mouseenter", {
          bubbles: false,
          cancelable: true,
          view: window,
        })
      );
      return Boolean(
        marker._tippy &&
          marker._tippy.state &&
          marker._tippy.state.isVisible
      );
    } catch (_error) {
      return false;
    } finally {
      setTimeout(function () {
        marker.__ambossSyntheticOpen = false;
      }, 0);
    }
  }

  function blockHoverAndFocus(event) {
    var marker = closestMarker(event.target);
    if (!marker) {
      return;
    }
    if (marker.__ambossSyntheticOpen) {
      return;
    }
    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }
    if (typeof event.stopPropagation === "function") {
      event.stopPropagation();
    }
  }

  function onClickCapture(event) {
    var marker = closestMarker(event.target);
    if (marker) {
      var instance = getOrCreateMarkerInstance(marker);

      if (
        instance &&
        instance.state &&
        instance.state.isVisible &&
        typeof instance.hide === "function"
      ) {
        instance.hide();
        stopEvent(event);
        return;
      }

      if (instance && typeof instance.show === "function") {
        patchInstance(instance);
        instance.show();
        if (instance.state && instance.state.isVisible) {
          stopEvent(event);
          return;
        }
      }

      if (showTooltipFromManagers(marker)) {
        stopEvent(event);
        return;
      }

      if (syntheticOpenFromClick(marker)) {
        stopEvent(event);
        return;
      }
      return;
    }

    if (isInsideTooltip(event.target)) {
      return;
    }

    hideAllTooltips();
  }

  function applyPatch() {
    installOneByOneStopPropagationBypass();
    patchManagers();
    patchExistingElements();
  }

  var previous = window.__ambossRequireClickState;
  if (previous) {
    if (Array.isArray(previous.listeners)) {
      for (var i = 0; i < previous.listeners.length; i += 1) {
        var listener = previous.listeners[i];
        document.removeEventListener(listener[0], listener[1], true);
      }
    }
    if (previous.observer && typeof previous.observer.disconnect === "function") {
      previous.observer.disconnect();
    }
    if (previous.timer) {
      clearInterval(previous.timer);
    }
  }

  var listeners = [];
  document.addEventListener("click", onClickCapture, true);
  listeners.push(["click", onClickCapture]);
  document.addEventListener("mouseover", blockHoverAndFocus, true);
  listeners.push(["mouseover", blockHoverAndFocus]);
  document.addEventListener("focusin", blockHoverAndFocus, true);
  listeners.push(["focusin", blockHoverAndFocus]);

  var observer = null;
  try {
    var root = document.querySelector(ROOT_SELECTOR) || document.documentElement;
    if (root && typeof MutationObserver === "function") {
      observer = new MutationObserver(function () {
        applyPatch();
      });
      observer.observe(root, { childList: true, subtree: true });
    }
  } catch (_error) {}

  applyPatch();

  var attempts = 0;
  var timer = setInterval(function () {
    attempts += 1;
    applyPatch();
    if (attempts >= 200) {
      clearInterval(timer);
    }
  }, 50);

  window.__ambossRequireClickState = {
    listeners: listeners,
    observer: observer,
    timer: timer,
  };
})();
"""


def _patch_amboss_tooltips(*_args) -> None:
    if mw and mw.reviewer and mw.reviewer.web:
        mw.reviewer.web.eval(_AMBOSS_TRIGGER_PATCH_JS)


gui_hooks.reviewer_did_show_question.append(_patch_amboss_tooltips)
gui_hooks.reviewer_did_show_answer.append(_patch_amboss_tooltips)
