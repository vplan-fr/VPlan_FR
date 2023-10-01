<script>
    import {notifications} from '../notifications.js';
    import {logged_in, active_modal, new_changelogs_available} from '../stores.js';
    import Dropdown from '../base_components/Dropdown.svelte';
    import { fly } from 'svelte/transition';
    import {customFetch, navigate_page} from "../utils.js";
    import {selected_favourite, favourites} from "../stores.js";

    function logout() {
        customFetch('/auth/logout')
            .then(data => {
                $logged_in = false;
            })
            .catch(error => {
                notifications.danger(error.message);
            });
    }
</script>

<nav transition:fly={{y:-64}}>
    <button class="logo-button" on:click={() => {navigate_page("plan"); selected_favourite.set(-1)}}>
        <img class="logo" src="/public/base_static/images/better_vp_white.svg" alt="Better VPlan Logo">
    </button>
    <ul class="nav-element-wrapper">
        <li><button on:click={() => {navigate_page("about_us")}} class="nav-button">Über uns</button></li>
        <li>
            <Dropdown let:toggle>
                <button slot="toggle_button" on:click={toggle} class="nav-button">
                    {#if $selected_favourite !== -1}
                        <!-- TODO: make different if some favourite selected -->
                        <span class="material-symbols-outlined">star</span>
                    {:else}
                        <span class="material-symbols-outlined">star</span>
                    {/if}
                </button>
                {#each $favourites as favourite, index}
                    <button class="nav-button" on:click={() => {selected_favourite.set(index); navigate_page("plan")}}>
                        {#if $selected_favourite === index}
                            <!-- TODO: make different if selected -->
                            <span class="material-symbols-outlined">star</span>
                        {:else}
                            <span class="material-symbols-outlined">star</span>
                        {/if}
                    ({index}) {favourite.name}</button>
                {/each}
                <button class="nav-button" on:click={() => navigate_page("favourites")}><span class="material-symbols-outlined">account_circle</span> Favoriten wählen</button>
            </Dropdown>
        </li>
        <li>
            <Dropdown let:toggle>
                <button slot="toggle_button" on:click={toggle} class="nav-button">
                    <span class="material-symbols-outlined" class:new_notification={$new_changelogs_available}>tune</span>
                </button>

                <button class="nav-button" on:click={() => $active_modal = "settings"}><span class="material-symbols-outlined">settings</span> Einstellungen</button>
                <button class="nav-button" on:click={() => navigate_page("school_manager")}><span class="material-symbols-outlined">school</span> Schule wechseln</button>
                <button class="nav-button" on:click={() => $active_modal = "preferences"}><span class="material-symbols-outlined">account_circle</span> Unterricht wählen</button>
                <button class="nav-button" on:click={() => $active_modal = "changelog"}><span class="material-symbols-outlined" class:new_notification={$new_changelogs_available}>assignment</span> Changelog {#if $new_changelogs_available}✨{/if}</button>
                <button class="nav-button" on:click={() => navigate_page("favourites")}><span class="material-symbols-outlined">account_circle</span> Favoriten wählen</button>
                <button class="nav-button" on:click={() => navigate_page("contact")}><span class="material-symbols-outlined">contact_page</span> Kontaktiere uns</button>
                <button on:click={logout} class="nav-button"><span class="material-symbols-outlined">logout</span> Logout</button>
            </Dropdown>
        </li>
    </ul>
</nav>

<style lang="scss">
    nav {
        z-index: 9999;
        background: var(--background);
        box-shadow: 0px 3px 4px rgba(0, 0, 0, 0.2);
        height: 64px;
        @media only screen and (max-width: 601px) {
            height: 56px;
            padding: 0px 5px;
        }
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        margin-right: calc(100% - 100vw);
        padding: 0px 20px;
        box-sizing: border-box;

        &::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.07);
            pointer-events: none;
        }

        .logo-button {
            height: 100%;
            box-sizing: border-box;
            border: none;
            background: transparent;
            .logo {
                box-sizing: border-box;
                height: 100%;
                padding: 10px;
                @media only screen and (max-width: 601px) {
                    padding: 8px;
                }
            }
        }

        .nav-element-wrapper {
            position: relative;
            display: flex;
            flex-direction: row;
            height: 100%;
            float: right;

            li {
                height: 100%;
                list-style-type: none;
            }
        }

        .nav-button {
            width: 100%;
            height: 100%;
            padding: 15px;
            background-color: transparent;
            border: none;
            font-size: var(--font-size-base);
            color: var(--text-color);
            transition: background-color 200ms ease;
            display: flex;
            flex-direction: row;
            justify-content: flex-start;
            align-items: center;
            gap: 10px;

            &:hover, &:focus-visible {
                background-color: rgba(0, 0, 0, 0.3);
            }

            span {
                position: relative;
                font-size: 1.4em;
            }
        }
    }
    .new_notification {
        position: relative;

        &::after {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            transform: translate(50%, -50%);
            background: var(--accent-color);
            width: 10px;
            aspect-ratio: 1;
            border-radius: 999vw;
        }
    }
</style>