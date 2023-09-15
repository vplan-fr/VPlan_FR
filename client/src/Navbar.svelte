<script>
    import {notifications} from './notifications.js';
    import {logged_in, current_page} from './stores.js';
    import Dropdown from './Components/Dropdown.svelte';
    import { fly } from 'svelte/transition';
    import { onMount } from 'svelte';
    import {customFetch} from "./utils.js";
    let error_hidden;

    function navigate_page(page_id) {
        $current_page = page_id;
        location.hash = `#${page_id}`;
    }

    function logout() {
        customFetch('/auth/logout')
            .then(data => {
                $logged_in = false;
                localStorage.setItem('logged_in', `${$logged_in}`);
            })
            .catch(error => {
                notifications.danger(error);
            });
    }

    window.addEventListener('popstate', (e) => {
        let new_location = location.hash.slice(1);
        if((new_location === "login" || new_location === "register") && logged_in) {
            e.preventDefault();
            history.go(1);
            return;
        }
        navigate_page(new_location);
    });

    onMount(() => {
        let new_location = location.hash.slice(1);
        if((new_location === "login" || new_location === "register") && logged_in) {
            return;
        }
        navigate_page(new_location);
    });
</script>

<nav transition:fly={{y:-64}}>
    <button class="logo-button" on:click={() => {navigate_page("plan")}}>
        <img class="logo" src="/base_static/images/better_vp_white.svg" alt="Better VPlan Logo">
    </button>
    <ul class="nav-element-wrapper">
        <li><button on:click={() => {navigate_page("about_us")}} class="nav-button">Über uns</button></li>
        <li>
            <Dropdown let:toggle>
                <button slot="toggle_button" on:click={toggle} class="nav-button">
                    <span class="material-symbols-outlined">tune</span>
                </button>

                <button class="nav-button" on:click={() => navigate_page("settings")}><span class="material-symbols-outlined">settings</span> Einstellungen</button>
                <button class="nav-button" on:click={() => navigate_page("school_manager")}><span class="material-symbols-outlined">school</span> Schule wechseln</button>
                <button class="nav-button" on:click={() => navigate_page("preferences")}><span class="material-symbols-outlined">account_circle</span> Unterricht wählen</button>
                <button on:click={logout} class="nav-button"><span class="material-symbols-outlined">logout</span> Logout</button>
            </Dropdown>
        </li>
    </ul>
</nav>

<style lang="scss">
    nav {
        z-index: 999;
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
                font-size: 1.4em;
            }
        }
    }
</style>