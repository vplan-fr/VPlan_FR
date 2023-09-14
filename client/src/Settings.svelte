<script>
    import {onMount} from "svelte";
    import {notifications} from "./notifications.js";
    import {logged_in, settings, title} from './stores.js';
    import {customFetch} from "./utils.js";

    let temp_settings;

    function change_settings() {
        customFetch("/auth/settings", {
            method: "POST",
            body: JSON.stringify($settings),
        })
            .then(data => {
                notifications.success("Einstellungen gespeichert")
            })
            .catch(error => {
                notifications.danger(error);
            })
    }
    
    function reset_settings() {
        customFetch("/auth/settings", {
            method: "DELETE"
        })
            .then(data => {
                $settings = data;
                temp_settings = data;
                notifications.success("Einstellungen zurückgesetzt");
            })
            .catch(error => {
                notifications.danger(error);
            })
    }
    
    function delete_account() {
        if(!confirm("Willst du wirklich deinen Account löschen?")) {return;}
        customFetch("/auth/account", {
            method: "DELETE"
        })
            .then(data => {
                notifications.success("Account gelöscht")
                $logged_in = false;
            })
            .catch(error => {
                notifications.danger(error);
            })
    }

    function view_saved_data() {
        window.open("/auth/account", "_blank");
    }

    onMount(() => {
        location.hash = "#settings";
        title.set("Einstellungen");
    });

    $: temp_settings = $settings;
    $: settings.set(temp_settings);
</script>

<main>
    <h1 class="responsive-heading">Einstellungen</h1>
    {#if temp_settings}
    <div class="settings-container">
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.normal_greetings}>Normale Begrüßungen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.chatgpt_greetings}>ChatGPT Begrüßungen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.day_switch_keys}>Pfeiltasten (Tastatur) zum Tag wechseln nutzen</span>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.background_color}>Hintergrundfarbe</span>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.accent_color}>Akzentfarbe</span>
        <br>
        <button on:click={change_settings} class="button" style="background-color: var(--accent-color);">Speichern</button>
        <div class="horizontal-container">
            <button on:click={reset_settings} class="button halfed">Einstellungen zurücksetzen</button>
            <button on:click={view_saved_data} class="button halfed">Gespeicherte Daten Einsehen</button>
        </div>
        <button on:click={delete_account} class="button" style="background-color: rgb(226, 109, 105);">Account löschen</button>
    </div>
    {:else}
    <span class="responsive-text">Einstellungen konnten nicht geladen werden.</span>
    {/if}
</main>

<style lang="scss">
    .settings-container {
        display: flex;
        flex-direction: column;
    }
    .horizontal-container {
        display: flex;
        flex-direction: row;
        
        .halfed {
            flex: 1;
        }
    }

    input[type="checkbox"], input[type="color"] {
        padding: 0;
        margin: 0;
        margin-right: 10px;
        width: var(--font-size-base);
        height: var(--font-size-base);
        border: 2px solid #5a5a5a;
    }

    input[type="color"] {
        -webkit-appearance: none;
    }
    input[type="color"]::-webkit-color-swatch-wrapper {
        padding: 0;
    }
    input[type="color"]::-webkit-color-swatch {
        border: none;
    }

    .button {
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        border: none;
        background-color: rgba(255, 255, 255, 0.2);
        color: var(--text-color);
        border-radius: 5px;
        padding: 10px;
        margin: 3px;
        font-size: var(--font-size-base);
        position: relative;

        .material-symbols-outlined {
            font-size: 1.3em;
            float: right;
            margin-left: .2em;
        }
    }
</style>