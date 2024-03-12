<script>
    import {new_changelogs_available, register_button_visible} from '../stores.js';
    import { fade } from 'svelte/transition';
    import Dropdown from '../base_components/Dropdown.svelte';
    import { fly } from 'svelte/transition';
    import {navigate_page} from "../utils.js";
    import Button from "../base_components/Button.svelte";
</script>

<nav transition:fly={{y:-64}}>
    <button class="logo-button" on:click={() => {navigate_page("");}}>
        <img class="logo" src="/public/base_static/images/better_vp_white.svg" alt="Better VPlan Logo">
    </button>
    <ul class="nav-element-wrapper">
        {#if !$register_button_visible}
            <li style="display: flex; align-items: center;" transition:fade={{duration: 100}}>
                <Button background="var(--accent-color)" on:click={() => navigate_page('login')}>
                    Anmelden
                </Button>
            </li>
        {/if}
        <li>
            <Dropdown>
                <button slot="toggle_button" let:toggle on:click={toggle} class="nav-button">
                    <span class="material-symbols-outlined" class:new_notification={$new_changelogs_available}>menu</span>
                </button>

                {#if $register_button_visible}
                    <button class="nav-button" on:click={() => navigate_page("login")}><span class="material-symbols-outlined">account_circle</span> Login</button>
                {/if}
                <button class="nav-button" on:click={() => navigate_page("about_us")}><span class="material-symbols-outlined">groups</span> Über uns</button>
                <button class="nav-button" on:click={() => navigate_page("contact")}><span class="material-symbols-outlined">contact_page</span> Kontaktiere uns</button>
                <button class="nav-button" on:click={() => navigate_page("impressum")}><span class="material-symbols-outlined">policy</span> Impressum</button>
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
  .favorite-selected {
    background: rgba(255, 255, 255, 0.2);
    outline: 4px solid rgba(255, 255, 255, 0.2);
    border-radius: 999vw;
  }
</style>