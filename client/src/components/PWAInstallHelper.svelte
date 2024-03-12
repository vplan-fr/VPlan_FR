<script>
    import { onMount } from "svelte";
    import { pwa_prompt, title } from "../stores";
    import { notifications } from "../notifications";
    import {navigate_page, update_hash} from "../utils";
    import Button from "../base_components/Button.svelte";

    async function try_install() {
        $pwa_prompt.prompt();
        const {outcome} = await $pwa_prompt.userChoice;
        $pwa_prompt = null;
        if(outcome === "accepted") {
            notifications.success("App erfolgreich installiert!");
            navigate_page('plan');
        } else if (outcome === "dismissed") {
            notifications.danger("App konnte nicht installiert werden.");
        }
    }

    onMount(() => {
        update_hash("pwa_install");
        title.set("Installieren");
    });
</script>

<main>
    <h1 class="responsive-heading">Füge uns zu deinem Homescreen hinzu</h1>
    {#if $pwa_prompt}
    <span class="responsive-text">
        Um <b>online</b> und <b>offline</b> schnell an deinen Stundenplan zu kommen, lade die Website als <b>App</b> herunter:
    </span>
    <Button on:click={try_install} id="pwa-install-btn" background="var(--accent-color)">Installieren <span class="material-symbols-outlined">install_mobile</span></Button>
    <button class="skip-btn" on:click={() => {navigate_page('plan')}}>Weiter</button>
    {:else}
    <span class="responsive-text">
        Um <b>online</b> und <b>offline</b> schnell an deinen Stundenplan zu kommen, lade die Website als <b>App</b> herunter:<br><br>
        <b>Für Apple-Geräte:</b>
        <ul>
            <li>Klicke auf den <div class="custom-badge">Seite Teilen Button <span class="material-symbols-outlined">ios_share</span></div></li>
            <li>Klicke auf <div class="custom-badge">Zum Homescreen hinzufügen <span class="material-symbols-outlined">add_box</span></div></li>
        </ul><br>
        <b>Für Android-Geräte:</b>
        <ul>
            <li>Klicke auf die <div class="custom-badge">drei Punkte (oben rechts) <span class="material-symbols-outlined">more_vert</span></div></li>
            <li>Klicke auf <div class="custom-badge">Zum Startbildschirm hinzufügen <span class="material-symbols-outlined">add_to_home_screen</span></div></li>
        </ul><br>
        <b>Für Desktop:</b>
        <ul>
            <li>Klicke in der Suchleiste (rechts) auf <div class="custom-badge">Better VPlan installieren <span class="material-symbols-outlined">install_desktop</span></div></li>
        </ul>
    </span>
    <Button on:click={() => {navigate_page('plan')}} background="var(--accent-color)" id="pwa-continue-btn">Weiter <span class="material-symbols-outlined">chevron_right</span></Button>
    {/if}
</main>

<style lang="scss">
    b {
        font-weight: 700;
    }

    .skip-btn {
        position: absolute;
        right: 20px;
        bottom: 20px;
        border: none;
        background: transparent;
        color: rgba(255, 255, 255, 0.6);
        font-size: var(--font-size-base);
    }

    :global(#pwa-install-btn) {
        margin: 15px auto !important;
    }
    
    :global(#pwa-continue-btn) {
        margin: 30px 0px 0px 15px;
    }

    .custom-badge {
        background: rgba(255, 255, 255, 0.07);
        padding: 10px 7px;
        border-radius: 5px;
        white-space: nowrap;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
    }
</style>