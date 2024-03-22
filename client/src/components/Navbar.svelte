<script>
    import {notifications} from '../notifications.js';
    import {logged_in, active_modal, new_changelogs_available, current_page} from '../stores.js';
    import Dropdown from '../base_components/Dropdown.svelte';
    import { fly } from 'svelte/transition';
    import {customFetch, navigate_page} from "../utils.js";
    import {selected_favorite, favorites, settings} from "../stores.js";

    function logout() {
        customFetch('/auth/logout')
            .then(data => {
                $logged_in = false;
            })
            .catch(error => {
                notifications.danger(error.message);
            });
    }

    let favorite_icon_map = {
        "forms": "school",
        "teachers": "elderly",
        "rooms": "sensor_door",
        "room_overview": "nest_multi_room"
    }
</script>

<nav transition:fly={{y:-64}}>
    <button class="logo-button" on:click={() => {navigate_page($settings.weekplan_default ? "weekplan" : "plan"); selected_favorite.set(-1)}}>
        <img class="logo" src="/public/base_static/images/better_vp_white.svg" alt="Better VPlan Logo">
    </button>
    <ul class="nav-element-wrapper">
        <li><button on:click={() => {
            navigate_page(
                ($current_page.startsWith("weekplan") || $current_page.startsWith("plan")) ?
                ($current_page.startsWith("weekplan") ? "plan" : "weekplan") :
                ($settings.weekplan_default ? "weekplan" : "plan"))}
            } class="nav-button"><span class="material-symbols-outlined">{
                ($current_page.startsWith("weekplan") || $current_page.startsWith("plan")) ?
                ($current_page.startsWith("weekplan") ? "calendar_view_day" : "calendar_view_week") :
                ($settings.weekplan_default ? "calendar_view_week" : "calendar_view_day")
        }</span></button></li>
        <li><button on:click={() => {navigate_page("about_us")}} class="nav-button">Über uns</button></li>
        <li>
            <Dropdown>
                <button slot="toggle_button" let:toggle on:click={toggle} class="nav-button">
                    <span class="material-symbols-outlined" class:favorite-selected={$selected_favorite !== -1}>star</span>
                </button>
                {#each $favorites as favorite, index}
                    <button class="nav-button" on:click={() => {
                        selected_favorite.set(index);
                        if(!$current_page.startsWith("weekplan")) navigate_page("plan");
                    }}>
                        <span class="material-symbols-outlined" class:favorite-selected={$selected_favorite === index}>{favorite_icon_map[favorite.plan_type]}</span>
                    {favorite.name}</button>
                {/each}
                <button class="nav-button" on:click={() => navigate_page("favorites")}><span class="material-symbols-outlined">settings</span> Favoriten verwalten</button>
            </Dropdown>
        </li>
        <li>
            <Dropdown>
                <button slot="toggle_button" let:toggle on:click={toggle} class="nav-button">
                    <span class="material-symbols-outlined" class:new_notification={$new_changelogs_available}>tune</span>
                </button>

                <button class="nav-button" on:click={() => $active_modal = "settings"}><span class="material-symbols-outlined">settings</span> Einstellungen</button>
                <button class="nav-button" on:click={() => navigate_page("school_manager")}><span class="material-symbols-outlined">school</span> Schule wechseln</button>
                <button class="nav-button" on:click={() => navigate_page("contact")}><span class="material-symbols-outlined">contact_page</span> Kontaktiere uns</button>
                <button class="nav-button" on:click={() => $active_modal = "changelog"}><span class="material-symbols-outlined" class:new_notification={$new_changelogs_available}>assignment</span> Changelog {#if $new_changelogs_available}✨{/if}</button>
                <button on:click={logout} class="nav-button"><span class="material-symbols-outlined">logout</span> Logout</button>
            </Dropdown>
        </li>
    </ul>
</nav>

<style lang="scss">
  nav {
    z-index: 9999;
    background: var(--background);
    box-shadow: 0 3px 4px rgba(0, 0, 0, 0.2);
    height: 64px;
    @media only screen and (max-width: 601px) {
      height: 56px;
      padding: 0 5px;
    }
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    margin-right: calc(100% - 100vw);
    padding: 0 20px;
    box-sizing: border-box;
    display: flex;
    flex-direction: row;
    justify-content: space-between;

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
      padding: 0 !important;

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