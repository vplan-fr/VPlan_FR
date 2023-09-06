<script>
    import {notifications} from './notifications.js';
    import {logged_in} from './stores.js';
    import Dropdown from './Dropdown.svelte';
    import { fly } from 'svelte/transition';

    function logout() {
        fetch('/logout')
            .then(response => response.json())
            .then(data => {
                $logged_in = !data["success"];
                localStorage.setItem('logged_in', `${$logged_in}`);
                if ($logged_in) {
                    error_hidden = false;
                    error_message = data["error"];
                }
            })
            .catch(error => {
                notifications.danger("Logout fehlgeschlagen!", 2000);
            });
    }
</script>

<nav transition:fly={{y:-64}}>
    <img class="logo" src="/base_static/images/better_vp_white.svg" alt="Better VPlan Logo">
    <ul class="nav-element-wrapper">
        <li>
            <Dropdown 
                let:onclick={onclick}>
                <button slot="toggle_button" on:click={onclick}>
                    <span class="material-symbols-outlined">tune</span>
                </button>

                <button><span class="material-symbols-outlined">settings</span> Einstellungen</button>
                <button><span class="material-symbols-outlined">account_circle</span> Unterricht wählen</button>
                <button on:click={logout}><span class="material-symbols-outlined">logout</span> Logout</button>
            </Dropdown>
        </li>
        <!-- <li><button on:click={togglePopup}>Manage Schools</button></li> -->
    </ul>
</nav>

<style lang="scss">
    nav {
        z-index: 999;
        background-color: var(--background-color);
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

        img.logo {
            box-sizing: border-box;
            height: 100%;
            padding: 10px;
            @media only screen and (max-width: 601px) {
                padding: 8px;
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
                button {
                    height: 100%;
                    padding: 15px;
                    background-color: transparent;
                    border: none;
                    font-size: 1rem;
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
        }
    }
</style>