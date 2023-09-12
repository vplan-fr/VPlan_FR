import { writable, derived } from "svelte/store"

const TIMEOUT = 3000

function createNotificationStore (timeout) {
    const _notifications = writable([])

    function send (message, type = "default", timeout=2000) {
        if (message.message) {
            message = message.message
        }
        _notifications.update(state => {
            return [...state, { id: id(), type, message, timeout }]
        })
    }

    let timers = []

    const notifications = derived(_notifications, ($_notifications, set) => {
        set($_notifications)
        if ($_notifications.length > 0) {
            const timer = setTimeout(() => {
                _notifications.update(state => {
                    state.shift()
                    return state
                })
            }, $_notifications[0].timeout)
            return () => {
                clearTimeout(timer)
            }
        }
    })
    const { subscribe } = notifications

    return {
        subscribe,
        send,
        default: (msg, timeout=2000) => send(msg, "default", timeout),
        danger: (msg, timeout=2000) => send(msg, "danger", timeout),
        warning: (msg, timeout=2000) => send(msg, "warning", timeout),
        info: (msg, timeout=2000) => send(msg, "info", timeout),
        success: (msg, timeout=2000) => send(msg, "success", timeout),
    }
}

function id() {
    return '_' + Math.random().toString(36).slice(2, 9);
};

export const notifications = createNotificationStore()