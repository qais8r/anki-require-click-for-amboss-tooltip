from aqt import gui_hooks, mw

_AMBOSS_TRIGGER_PATCH_JS = r"""
(() => {
  const apply = () => {
    if (!window.ambossAddon || !ambossAddon.tooltip || !ambossAddon.tooltip.tooltips) {
      return false;
    }
    const tooltips = ambossAddon.tooltip.tooltips;
    if (tooltips.tippyOptions) {
      tooltips.tippyOptions.trigger = 'click';
    }
    const selector = tooltips.selector || '#qa';
    const root = document.querySelector(selector);
    if (root && root._tippy && typeof root._tippy.setProps === 'function') {
      root._tippy.setProps({ trigger: 'click' });
    }
    return true;
  };

  if (apply()) {
    return;
  }

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    if (apply() || attempts >= 20) {
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
