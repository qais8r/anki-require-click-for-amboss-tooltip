from aqt import gui_hooks, mw

_AMBOSS_TRIGGER_PATCH_JS = r"""
(function () {
  var FORCE_TRIGGER = "click";

  function setTriggerOnOptions(options) {
    if (!options || typeof options !== "object") {
      return false;
    }
    options.trigger = FORCE_TRIGGER;
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

  function patchExistingTippies(root) {
    if (!root || typeof root.querySelectorAll !== "function") {
      return false;
    }

    var patched = patchElementTippy(root);
    var elements = root.querySelectorAll("*");
    for (var i = 0; i < elements.length; i += 1) {
      if (patchElementTippy(elements[i])) {
        patched = true;
      }
    }
    return patched;
  }

  function findClosestMarker(target, markerSelector) {
    if (!target || !markerSelector) {
      return null;
    }

    var node = target;
    if (node.nodeType === 3) {
      node = node.parentElement;
    }

    if (node && typeof node.closest === "function") {
      return node.closest(markerSelector);
    }

    while (node && node !== document) {
      if (
        node.nodeType === 1 &&
        typeof node.matches === "function" &&
        node.matches(markerSelector)
      ) {
        return node;
      }
      node = node.parentNode;
    }
    return null;
  }

  function showTooltipOnClick(marker, manager) {
    if (!marker) {
      return false;
    }

    try {
      patchInstance(marker._tippy);
      if (marker._tippy && typeof marker._tippy.show === "function") {
        marker._tippy.show();
        return true;
      }

      if (manager && typeof manager.showTooltipOnElement === "function") {
        manager.showTooltipOnElement(marker);
        return true;
      }

      var addon = window.ambossAddon && window.ambossAddon.tooltip;
      if (addon && addon.tooltips && typeof addon.tooltips.showTooltipOnElement === "function") {
        addon.tooltips.showTooltipOnElement(marker);
        return true;
      }
      if (addon && typeof addon.showTooltipOnElement === "function") {
        addon.showTooltipOnElement(marker);
        return true;
      }
    } catch (_error) {}

    return false;
  }

  function installClickGate(manager) {
    var selector = (manager && manager.selector) || "#qa";
    if (typeof selector !== "string") {
      return false;
    }

    var root = document.querySelector(selector);
    if (!root) {
      return false;
    }
    if (root.__ambossForceClickGateInstalled) {
      return true;
    }

    var markClass = (manager && manager.markClass) || "amboss-marker";
    var markerSelector = "." + markClass;

    var blockHoverAndFocus = function (event) {
      var marker = findClosestMarker(event.target, markerSelector);
      if (!marker) {
        return;
      }
      if (typeof event.stopImmediatePropagation === "function") {
        event.stopImmediatePropagation();
      }
      if (typeof event.stopPropagation === "function") {
        event.stopPropagation();
      }
    };

    root.addEventListener("mouseover", blockHoverAndFocus, true);
    root.addEventListener("mousemove", blockHoverAndFocus, true);
    root.addEventListener("mouseenter", blockHoverAndFocus, true);
    root.addEventListener("focusin", blockHoverAndFocus, true);

    root.addEventListener(
      "click",
      function (event) {
        var marker = findClosestMarker(event.target, markerSelector);
        if (!marker) {
          return;
        }
        showTooltipOnClick(marker, manager);
      },
      true
    );

    root.__ambossForceClickGateInstalled = true;
    return true;
  }

  function patchDeckTemplateController(controller) {
    if (!controller || typeof controller !== "object") {
      return false;
    }

    var patched = false;
    var tooltipManager = controller.ambossTooltips;
    if (!tooltipManager || typeof tooltipManager !== "object") {
      return false;
    }

    if (setTriggerOnOptions(tooltipManager.tippyOptions)) {
      patched = true;
    }
    if (tooltipManager.tippyOptions && typeof tooltipManager.tippyOptions === "object") {
      tooltipManager.tippyOptions.trigger = FORCE_TRIGGER;
      patched = true;
    }

    if (
      !tooltipManager.__forceClickPatched &&
      typeof tooltipManager.initialize === "function"
    ) {
      var originalInitialize = tooltipManager.initialize;
      tooltipManager.initialize = function () {
        setTriggerOnOptions(this && this.tippyOptions);
        if (this && this.tippyOptions) {
          this.tippyOptions.trigger = FORCE_TRIGGER;
        }
        var value = originalInitialize.apply(this, arguments);
        var root = document.querySelector((this && this.selector) || "#qa");
        if (root) {
          patchInstance(root._tippy);
        }
        return value;
      };
      tooltipManager.__forceClickPatched = true;
      patched = true;
    }

    if (installClickGate(tooltipManager)) {
      patched = true;
    }

    var root = document.querySelector((tooltipManager && tooltipManager.selector) || "#qa");
    if (root && patchInstance(root._tippy)) {
      patched = true;
    }

    return patched;
  }

  function patchManager(manager) {
    if (!manager || (typeof manager !== "object" && typeof manager !== "function")) {
      return false;
    }

    var patched = false;

    if (setTriggerOnOptions(manager.tippyOptions)) {
      patched = true;
    }
    if (setTriggerOnOptions(manager.delegateOptions)) {
      patched = true;
    }

    if (Array.isArray(manager.instances)) {
      for (var i = 0; i < manager.instances.length; i += 1) {
        if (patchInstance(manager.instances[i])) {
          patched = true;
        }
      }
    }

    if (installClickGate(manager)) {
      patched = true;
    }

    var selector = manager.selector || "#qa";
    if (typeof selector === "string") {
      var root = document.querySelector(selector);
      if (root) {
        if (patchInstance(root._tippy)) {
          patched = true;
        }
        if (patchExistingTippies(root)) {
          patched = true;
        }
      }
    }

    if (!manager.__forceClickPatched && typeof manager.initialize === "function") {
      var originalInitialize = manager.initialize;
      manager.initialize = function () {
        setTriggerOnOptions(this && this.tippyOptions);
        var value = originalInitialize.apply(this, arguments);
        var root = document.querySelector((this && this.selector) || "#qa");
        if (root) {
          patchInstance(root._tippy);
        }
        return value;
      };
      manager.__forceClickPatched = true;
      patched = true;
    }

    if (
      !manager.__forceClickCreatePatched &&
      typeof manager._createTippyOnElement === "function"
    ) {
      var originalCreateTippyOnElement = manager._createTippyOnElement;
      manager._createTippyOnElement = function (element) {
        setTriggerOnOptions(this && this.tippyOptions);
        var instance = originalCreateTippyOnElement.call(this, element);
        patchInstance(instance);
        return instance;
      };
      manager.__forceClickCreatePatched = true;
      patched = true;
    }

    return patched;
  }

  function apply() {
    var patched = false;
    var addon = window.ambossAddon && window.ambossAddon.tooltip;
    if (addon) {
      if (patchManager(addon)) {
        patched = true;
      }
      if (patchManager(addon.tooltips)) {
        patched = true;
      }
      if (patchManager(addon.default)) {
        patched = true;
      }

      if (installClickGate(addon.tooltips || addon)) {
        patched = true;
      }
    }

    if (patchDeckTemplateController(window.ambossController)) {
      patched = true;
    }

    var qa = document.querySelector("#qa");
    if (qa) {
      if (patchInstance(qa._tippy)) {
        patched = true;
      }
      if (patchExistingTippies(qa)) {
        patched = true;
      }
      if (installClickGate(null)) {
        patched = true;
      }
    }

    return patched;
  }

  apply();
  var attempts = 0;
  var timer = setInterval(function () {
    attempts += 1;
    apply();
    if (attempts >= 300) {
      clearInterval(timer);
    }
  }, 50);
})();
"""


def _patch_amboss_tooltips(*_args) -> None:
    if mw and mw.reviewer and mw.reviewer.web:
        mw.reviewer.web.eval(_AMBOSS_TRIGGER_PATCH_JS)


gui_hooks.reviewer_did_show_question.append(_patch_amboss_tooltips)
gui_hooks.reviewer_did_show_answer.append(_patch_amboss_tooltips)
