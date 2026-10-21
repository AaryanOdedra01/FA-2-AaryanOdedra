"""Optional desktop notifications using a small, local Streamlit v2 component.

The permission prompt runs only from a user's click. No push service or network
request is involved; Python remains responsible for scheduling drink reminders.
"""

import streamlit as st


_ALERTS_JS = """
export default function(component) {
    const {parentElement, data} = component;
    const button = parentElement.querySelector('button');
    const status = parentElement.querySelector('[role="status"]');
    const supported = ('Notification' in window) && window.isSecureContext;
    const show = (message) => { status.textContent = message; };
    const update = () => {
        if (!supported) {
            button.disabled = true;
            show('Browser alerts are unavailable here. In-app reminders still work.');
        } else if (Notification.permission === 'granted') {
            button.disabled = true;
            button.textContent = 'Browser alerts allowed';
            show('Alerts use your browser’s permission. Keep the app open.');
        } else if (Notification.permission === 'denied') {
            button.disabled = true;
            show('Browser alerts are blocked. You can change this in your browser’s site settings.');
        } else {
            button.disabled = !data.enabled;
            show(data.enabled ? 'Optional: allow desktop alerts for this site.' : 'Enable drink reminders above to set up browser alerts.');
        }
    };
    parentElement.querySelector('.browser-alert-controls').hidden = !data.controls;
    update();
    button.onclick = async () => {
        try { await Notification.requestPermission(); update(); }
        catch (_) { show('This browser could not enable desktop alerts. In-app reminders still work.'); }
    };
    if (data.event && supported && Notification.permission === 'granted') {
        let seen = null;
        try { seen = sessionStorage.getItem('waterbuddy-last-alert'); } catch (_) {}
        const memory = window.__waterBuddyDeliveredAlerts || (window.__waterBuddyDeliveredAlerts = new Set());
        if (seen !== data.event.id && !memory.has(data.event.id)) {
            try {
                const alert = new Notification(data.event.title, {body:data.event.body, tag:'waterbuddy-drink'});
                memory.add(data.event.id);
                alert.onclick = () => { window.focus(); alert.close(); };
                setTimeout(() => alert.close(), 12000);
                try { sessionStorage.setItem('waterbuddy-last-alert', data.event.id); } catch (_) {}
            } catch (_) { show('Desktop alerts are unavailable on this device. In-app reminders still work.'); }
        }
    }
    return () => { button.onclick = null; };
}
"""

_alerts = st.components.v2.component(
    "waterbuddy_browser_alerts",
    html='<div class="browser-alert-controls"><button type="button">Allow browser alerts</button><p role="status" aria-live="polite"></p></div>',
    css="""
    .browser-alert-controls button {font:500 13px 'Segoe UI',sans-serif; background:var(--card); color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:10px 14px; cursor:pointer; transition:transform .1s,border-color .15s}
    .browser-alert-controls button:hover:not(:disabled) {border-color:var(--teal)} .browser-alert-controls button:active:not(:disabled) {transform:scale(.975)} .browser-alert-controls button:disabled {opacity:.6;cursor:default}
    .browser-alert-controls button:focus-visible {outline:2px solid var(--teal);outline-offset:3px}
    .browser-alert-controls p {font:12px/1.5 'Segoe UI',sans-serif;color:var(--muted);margin:8px 0 0}
    @media(prefers-reduced-motion:reduce) {.browser-alert-controls button {transition:none} .browser-alert-controls button:active {transform:none}}
    """,
    js=_ALERTS_JS,
    isolate_styles=False,
)


def browser_alerts(*, event=None, controls=False, enabled=False, key="browser_delivery"):
    _alerts(data={"event": event, "controls": controls, "enabled": enabled}, key=key)
