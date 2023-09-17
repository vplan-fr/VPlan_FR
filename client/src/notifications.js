import {notifications_list} from "./stores.js";

const TIMEOUT = 3000

function id() {
    return '_' + Math.random().toString(36).slice(2, 9);
}

export function removeNotification(id) {
    notifications_list.update(arr => arr.filter(item => item.id !== id));
}

function send(msg, type="default", timeout=2000) {
    let cur_id = id();
    notifications_list.update( arr => [...arr, {"message": msg, "type": type, id: cur_id}])
    setTimeout(() => {
        notifications_list.update(arr => arr.filter(item => item.id !== cur_id));
    }, timeout);
}

export const notifications = {
    send,
    default: (msg, timeout=2000) => send(msg, "default", timeout),
    danger: (msg, timeout=2000) => send(msg, "danger", timeout),
    warning: (msg, timeout=2000) => send(msg, "warning", timeout),
    info: (msg, timeout=2000) => send(msg, "info", timeout),
    success: (msg, timeout=2000) => send(msg, "success", timeout),
}
