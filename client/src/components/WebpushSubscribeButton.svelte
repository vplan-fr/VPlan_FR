<script>
    import {customFetch} from "../utils.js";
    import {notifications} from "../notifications.js";

    let webpush_public_key = null
    customFetch("/api/v69.420/get_webpush_public_key").then(
        res => webpush_public_key = res
    )
</script>

{#if !webpush_public_key}
    <button disabled>Laden...</button>
{:else}
    <button on:click={
        async () => {
            let sw = await navigator.serviceWorker.ready;
            customFetch("/api/v69.420/add_webpush_subscription", {"method": "POST", "body": JSON.stringify(
                await sw.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: webpush_public_key
                })
            )})
                .then(data => {
                    notifications.success("Push-Benachrichtigungen aktiviert.")
                })
                .catch(error => {
                    notifications.danger(`Fehler: ${error}`)
                })
        }
    } class="nav-button">Push-Benachrichtigungen einschalten
    </button>
{/if}
