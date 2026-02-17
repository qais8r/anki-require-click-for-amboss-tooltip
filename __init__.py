from aqt import gui_hooks, mw

_AMBOSS_TRIGGER_PATCH_JS = r"""
(() => {
  const FORCE_TRIGGER = 'click';

  const patchInstance = (instance) => {
    if (!instance || typeof instance.setProps !== 'function') {
      return false;
    }
    instance.setProps({ trigger: FORCE_TRIGGER });
    return true;
  };

  const patchElementTippy = (el) => patchInstance(el && el._tippy);

  const patchExistingTippies = (root) => {
    if (!root) {
      return false;
    }
    let patched = patchElementTippy(root);
    for (const el of root.querySelectorAll('*')) {
      patched = patchElementTippy(el) || patched;
    }
    return patched;
  };

  const apply = () => {
    if (!window.ambossAddon || !ambossAddon.tooltip || !ambossAddon.tooltip.tooltips) {
      return false;
    }
    const tooltips = ambossAddon.tooltip.tooltips;
    if (tooltips.tippyOptions) {
      tooltips.tippyOptions.trigger = FORCE_TRIGGER;
    }
    if (tooltips.delegateOptions) {
      tooltips.delegateOptions.trigger = FORCE_TRIGGER;
    }
    if (Array.isArray(tooltips.instances)) {
      for (const instance of tooltips.instances) {
        patchInstance(instance);
      }
    }
    const selector = tooltips.selector || '#qa';
    const root = document.querySelector(selector);
    patchExistingTippies(root);
    return true;
  };

  if (apply()) {
    return;
  }

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    if (apply() || attempts >= 100) {
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
