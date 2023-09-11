<script>
    import {notifications} from "./notifications.js";
    import {settings} from './stores.js';

    import {customFetch, get_settings} from "./utils.js";

    let local_settings = $settings;
    function change_settings() {
        customFetch("/settings", {
            method: "POST",
            body: JSON.stringify($settings),
        })
            .then(data => {
                notifications.info("Einstellungen gespeichert")
            })
            .catch(error => {
                notifications.danger(error)
                get_settings();
            })
    }

    $: get_settings();
    $: settings.set(local_settings);
</script>

<main>
    <button on:click={change_settings}>Speichern</button>
    <br>
    ChatGPT greetings: <input type="checkbox" bind:checked={local_settings.chatgpt_greetings}><br>
    show plan toasts: <input type="checkbox" bind:checked={local_settings.show_plan_toasts}><br>
    day switch keys: <input type="checkbox" bind:checked={local_settings.day_switch_keys}><br>
    background color: <input type="color" bind:value={local_settings.background_color}><br>
    accent color: <input type="color" bind:value={local_settings.accent_color}>
</main>

<style lang="scss">


</style>