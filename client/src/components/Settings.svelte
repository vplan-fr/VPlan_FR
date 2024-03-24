<script>
    import {notifications} from "../notifications.js";
    import {logged_in, settings, active_modal} from '../stores.js';
    import {clear_plan_cache, customFetch, update_colors} from "../utils.js";
    import Modal from "../base_components/Modal.svelte";
    import Button from "../base_components/Button.svelte";
    import {get_webpush_public_key, webpush_subscribe, webpush_unsubscribe, webpush_unsubscribe_all, webpush_test} from "../webpush_handler.js";

    let temp_settings;
    let is_admin = false;

    customFetch("/auth/is_admin")
        .then(data => {
            is_admin = data;
        })
        .catch(error =>{});

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

    $: update_colors(temp_settings);
</script>

<Modal id="settings" onopen={cancel_setting_changes} onclose={cancel_setting_changes}>
    <h1 class="responsive-heading">Einstellungen</h1>
    {#if temp_settings}
    <div class="settings-container">
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.normal_greetings}>Normale Begrüßungen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.chatgpt_greetings}>ChatGPT Begrüßungen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.load_first_favorite}>Beim Start den ersten Favoriten laden</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.weekplan_default}>Standardmäßig den Wochenplan öffnen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.swipe_day_change}>Swipen um Tag zu wechseln</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.day_switch_keys}>Pfeiltasten (Tastatur) zum Tag wechseln nutzen</span>
        <h2 class="category-heading">Aussehen</h2>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.background_color}>Hintergrundfarbe</span>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.text_color}>Textfarbe</span>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.accent_color}>Akzentfarbe</span>
        <span class="responsive-text"><input type="color" bind:value={temp_settings.cancelled_color}>Ausfallfarbe</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.external_times}>Externe Unterrichtszeiten</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.filled_in_buttons}>Ausgefüllte Buttons (Bei Änderungen / Ausfall)</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.filled_in_weekplan}>Unterrichtsstunden füllen die komplette Breite beim Wochenplan</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.rainbow}>Regenbogen 🌈</span>
        <h2 class="category-heading">Nerd Section</h2>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.show_revision_selector}>Planversion auswählbar machen</span>
        <span class="responsive-text"><input type="checkbox" bind:checked={temp_settings.use_grouped_form_plans}>Lehrer/Raumpläne nur als umgeordnete Klassenpläne anzeigen. (Bsp.: Lehreränderung bei Klassenplan wird nicht zu Ausfall im Lehrerplan des ursprünglichen Lehrers)</span>
        {#if is_admin}
            <h2 class="category-heading">Admin-Section</h2>
            <h2 class="category-heading">Push-Benachrichtigungen</h2>
            <Button on:click={
                async () => {
                    await webpush_subscribe(await get_webpush_public_key());
                }
            } class="nav-button">für diesen Browser einschalten
            </Button>
            <Button on:click={
                async () => {
                    await webpush_unsubscribe(await get_webpush_public_key());
                }
            } class="nav-button">für diesen Browser ausschalten
            </Button>
            <Button on:click={
                async () => {
                    await webpush_unsubscribe_all(await get_webpush_public_key());
                }
            } class="nav-button">für alle Browser ausschalten
            </Button>
            <Button on:click={
                async () => {
                    await webpush_test(await get_webpush_public_key());
                }
            } class="nav-button">Push-Benachrichtigungen testen
            </Button>
        {/if}
        <br>
        <div class="horizontal-container">
            <Button on:click={reset_settings} class="split">Einstellungen zurücksetzen</Button>
            <Button on:click={() => {clear_plan_cache(() => {notifications.success("Cache geleert");})}} class="split">Plan-Cache leeren</Button>
            <Button on:click={view_saved_data} class="split">Gespeicherte Daten einsehen</Button>
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
        
        :global(.split) {
            flex: 1;
        }
    }

    .category-heading {
        font-size: var(--font-size-lg);
        font-weight: 700;
        margin: 10px 0px;
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