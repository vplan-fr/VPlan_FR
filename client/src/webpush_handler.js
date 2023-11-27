import {customFetch} from "./utils.js";
import {notifications} from "./notifications.js";


export async function get_webpush_public_key() {
    return await customFetch("/api/v69.420/get_webpush_public_key")
}


export async function webpush_subscribe(public_key) {
    let sw = await navigator.serviceWorker.ready;

    customFetch("/api/v69.420/webpush_subscription", {
        "method": "POST", "body": JSON.stringify(
            await sw.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: public_key
            })
        )
    })
        .then(data => {
            notifications.success("Push-Benachrichtigungen für diesen Broswer aktiviert.")
        })
        .catch(error => {
            notifications.danger(`Fehler: ${error}`)
        })
}

export async function webpush_unsubscribe(public_key) {
    let sw = await navigator.serviceWorker.ready;

    customFetch("/api/v69.420/webpush_subscription", {
        "method": "DELETE", "body": JSON.stringify(
            await sw.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: public_key
            })
        )
    })
        .then(data => {
            notifications.success("Push-Benachrichtigungen für diesen Browser deaktiviert.")
        })
        .catch(error => {
            notifications.danger(`Fehler: ${error}`)
        })
}

export async function webpush_unsubscribe_all(public_key) {
    let sw = await navigator.serviceWorker.ready;

    customFetch("/api/v69.420/webpush_subscription", {
        "method": "DELETE", "body": "__all__"
    })
        .then(data => {
            notifications.success("Push-Benachrichtigungen für alle Browser deaktiviert.")
        })
        .catch(error => {
            notifications.danger(`Fehler: ${error}`)
        })
}
