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
    if (!addon) {
      return false;
    }

    if (patchManager(addon)) {
      patched = true;
    }
    if (patchManager(addon.tooltips)) {
      patched = true;
    }
    if (patchManager(addon.default)) {
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
    }

    return patched;
  }

  if (apply()) {
    return;
  }

  var attempts = 0;
  var timer = setInterval(function () {
    attempts += 1;
    if (apply() || attempts >= 300) {
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
