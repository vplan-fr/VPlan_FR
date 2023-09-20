<script>
    import {notifications} from "./notifications.js";
    import {logged_in, settings, active_modal} from './stores.js';
    import {customFetch, update_colors} from "./utils.js";
    import Modal from "./Components/Modal.svelte";
    import { onMount } from "svelte";
    import Button from "./Components/Button.svelte";

    let temp_settings;

    function change_settings() {
        $settings = structuredClone(temp_settings);
        customFetch("/auth/settings", {
            method: "POST",
            body: JSON.stringify($settings),
        })
            .then(data => {
                notifications.success("Einstellungen gespeichert")
            })
            .catch(error => {
                notifications.danger(error.message);
            })
    }
    
    function reset_settings() {
        customFetch("/auth/settings", {
            method: "DELETE"
        })
            .then(data => {
                $settings = structuredClone(data);
                temp_settings = structuredClone(data);
                notifications.success("Einstellungen zurückgesetzt");
            })
            .catch(error => {
                notifications.danger(error.message);
            })
    }

    function cancel_setting_changes() {
        temp_settings = structuredClone($settings);
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
                notifications.danger(error.message);
            })
    }

    function view_saved_data() {
        window.open("/auth/account", "_blank");
    }

    // onMount(() => {
    //     console.log("Mounted Settings.svelte");
    // });

    $: update_colors(temp_settings);
</script>

<Modal id="settings" onopen={cancel_setting_changes} onclose={cancel_setting_changes}>
    <h1 class="responsive-heading">Einstellungen</h1>
    {#if temp_settings}
    <div class="settings-container">
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.normal_greetings}>Normale Begrüßungen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.chatgpt_greetings}>ChatGPT Begrüßungen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.show_revision_selector}>Planversion auswählbar machen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.use_grouped_form_plans}>Lehrer/Raumpläne nur als umgeordnete Klassenpläne anzeigen. (Bsp.: Lehreränderung bei Klassenplan wird nicht zu Ausfall im Lehrerplan des ursprünglichen Lehrers)</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.day_switch_keys}>Pfeiltasten (Tastatur) zum Tag wechseln nutzen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.rainbow}>Regenbogen 🌈</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.filled_in_buttons}>Ausgefüllte Buttons (Bei Änderungen / Ausfall)</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.swipe_day_change}>Swipen um Tag zu wechseln</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.external_times}>Externe Unterrichtszeiten</span>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.background_color}>Hintergrundfarbe</span>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.text_color}>Textfarbe</span>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.accent_color}>Akzentfarbe</span>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.cancelled_color}>Ausfallfarbe</span>
        <br>
        <div class="horizontal-container">
            <Button on:click={reset_settings} class="halfed">Einstellungen zurücksetzen</Button>
            <Button on:click={view_saved_data} class="halfed">Gespeicherte Daten einsehen</Button>
        </div>
        <Button on:click={delete_account} background="var(--cancelled-color)">Account löschen</Button>
    </div>
    {:else}
    <span class="responsive-text">Einstellungen konnten nicht geladen werden.</span>
    {/if}
    <svelte:fragment slot="footer">
        <Button on:click={() => {change_settings(); $active_modal = ""}} background="var(--accent-color)" small={true}>Speichern</Button>
        <Button on:click={() => {$active_modal = ""}} small={true}>Abbrechen</Button>
    </svelte:fragment>
</Modal>

<style lang="scss">
    .settings-container {
        display: flex;
        flex-direction: column;
    }
    .horizontal-container {
        display: flex;
        flex-direction: row;
        
        :global(.halfed) {
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
</style>