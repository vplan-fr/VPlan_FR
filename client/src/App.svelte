<script>
    import Plan from "./components/Plan.svelte";
    import Weekplan from "./components/Weekplan.svelte";
    import Authentication from "./components/Authentication.svelte";
    import LandingPage from "./components/LandingPage.svelte";
    import LandingPageNavbar from "./components/LandingPageNavbar.svelte";
	import Toast from './base_components/Toast.svelte';
    import Navbar from "./components/Navbar.svelte";
    import Settings from "./components/Settings.svelte";
    import AboutUs from "./components/AboutUs.svelte";
    import Favorites from "./components/Favorites.svelte";
    import Stats from "./Dashboard/Stats/Stats.svelte";
    import SveltyPicker from 'svelty-picker';
    import {get_settings, group_rooms, update_colors, navigate_page, init_indexed_db, clear_plan_cache, get_favorites} from "./utils.js";
    import {notifications} from './notifications.js';
    import {logged_in, title, current_page, settings, active_modal, pwa_prompt, indexed_db, selected_favorite, favorites} from './stores.js'
    import SchoolManager from "./components/SchoolManager.svelte";
    import Changelog from "./components/Changelog.svelte";
    import Select from "./base_components/Select.svelte";
    import Contact from "./components/Contact.svelte";
    import Impressum from "./components/Impressum.svelte";
    import {customFetch, format_revision_date, load_meta} from "./utils.js";
    import {de} from 'svelty-picker/i18n';
    import PwaInstallHelper from "./components/PWAInstallHelper.svelte";
    import Dropdown from "./base_components/Dropdown.svelte";
    import {animateScroll} from 'svelte-scrollto-element';
    import Button from "./base_components/Button.svelte";
    import { fade } from "svelte/transition";
    import FancyBackground from "./components/FancyBackground.svelte";
    import NotFound from "./components/NotFound.svelte";

    const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s);
    let school_num;
    let date;
    let all_revisions;
    let plan_type;
    let plan_value;
    let teacher_dict;
    let all_rooms;
    let grouped_forms;
    let api_base;
    let selected_revision;
    let meta;
    let enabled_dates;
    let grouped_rooms;
    let course_lists;
    let selected_teacher;
    let selected_room;
    let selected_form;
    let footer_padding;
    let emoji;
    let greeting;
    let form_arr;
    let teacher_arr;
    let room_arr;
    let revision_arr;
    let available_plan_version;
    const available_plan_version_map = {
        "cached": "Offline Plan",
        "network_cached": "Aktueller Plan",
        "network_uncached": "Online only Plan"
    };
    let load_favorite = false;

    function init_vars() {
        school_num = localStorage.getItem('school_num');
        date = null;
        all_revisions = [".newest"];
        plan_type = null;
        plan_value = null;
        teacher_dict = {};
        all_rooms = null;
        grouped_forms = [];
        api_base = null;
        selected_revision = ".newest";
        meta = {};
        enabled_dates = [];
        grouped_rooms = [];
        course_lists = {};
        selected_teacher = null;
        selected_room = null;
        selected_form = null;
        footer_padding = false;
        emoji = get_emoji();
        greeting = "";
        form_arr = [];
        teacher_arr = [];
        room_arr = [];
        revision_arr = [];
    }

    function get_meta(tmp_school_num) {
        load_meta(tmp_school_num)
            .then(data => {
                if (!data) {
                    return
                }
                meta = data[0];
                all_rooms = meta.rooms;
                teacher_dict = meta.teachers;
                grouped_forms = meta.forms.grouped_forms;
                enabled_dates = Object.keys(meta.dates);
                if(!date) {
                    date = meta.date;
                }
                course_lists = meta.forms.forms;
                //data_from_cache = data[1];
            })
            .catch(error => {
                if (data_from_cache) {
                    // notifications.info("Metadaten aus Cache geladen", 2000);
                    console.log("Metadaten aus Cache geladen");
                } else {
                    notifications.danger(error.message);
                }
            });
    }

    function check_login_status() {
        customFetch('/auth/check_login')
            .then(data => {
                if(data["logged_in"] !== $logged_in) {
                    $logged_in = data["logged_in"];
                    localStorage.setItem('logged_in', `${$logged_in}`);
                }
            })
            .catch(error => {
                //notifications.danger(error);
                console.error("Login-Status konnte nicht überprüft werden");
            }
        );
    }

    function choose(choices) {
        var index = Math.floor(Math.random() * choices.length);
        return choices[index];
    }

    function get_emoji() {
        let curr_date = new Date();
        let curr_day = curr_date.getDay();
        let curr_hours = curr_date.getHours();
        let emoji = "👋";
        if(curr_day <= 5 && curr_day > 0 && curr_hours <= 17) {
            emoji = choose(["👨‍🏫", "👩‍🏫"]);
        }
        if (curr_hours >= 4 && curr_hours < 8) {
            emoji = "🥱";
            if(curr_day === 1) {
                emoji = "😴";
            }
        }
        if (curr_hours >= 20 || curr_hours < 4) {
            emoji = "😴";
        }
        if(
            (curr_day === 5 && curr_hours >= 20) ||
            (curr_day === 6 && (curr_hours >= 20 || curr_hours < 4)) ||
            (curr_day === 0 && curr_hours < 4)
        ) {
            emoji = choose(["🕺", "💃", "🎮", "🎧"]);
        }
        return emoji;
    }

    function get_greeting() {
        customFetch("/auth/greeting")
            .then(data => {
                greeting = data;
            })
            .catch(error => {
                greeting = choose([
                    "Wir sind selbst offline hier für dich!",
                    "Ahoi, du Offline-Abenteurer",
                    "Off-the-Grid 😲, wie ist es da draußen?",
                    "Schüler-WLAN tot?"
                ]);
                console.error("Begrüßung konnte nicht geladen werden.");
            })
    }

    function close_modal() {
        $active_modal = "";
    }

    function scrollTo(element) {
        // Disable on Desktop (aspect ratio > 1)
        if ((window.innerWidth > window.innerHeight) || !element) {return;}
        var headerOffset = window.innerWidth > 601 ? -74 : -66;

        animateScroll.scrollTo({element: element, offset: headerOffset, duration: 200});
    }

    function set_plan(new_plan_type, new_plan_value) {
        plan_type = new_plan_type;
        plan_value = new_plan_value;
        scrollTo(document.getElementsByClassName("plan")[0]);
    }

    function gen_form_arr(grouped_forms) {
        form_arr = [];
        for (const [form_group, forms] of Object.entries(grouped_forms)) {
            let converted_forms = [];
            for(let form of forms) {
                converted_forms.push({"id": form, "display_name": form});
            }
            form_arr.push([form_group !== "null" ? form_group : "Sonstige", converted_forms]);
        }
    }

    function gen_teacher_arr(teacher_dict) {
        teacher_arr = [];
        for(let teacher of Object.values(teacher_dict)) {
            let long_name = teacher.full_surname || teacher.plan_long;
            let display_name = teacher.plan_short;

            if (long_name != null) {
                display_name += ` (${long_name})`;
            }

            teacher_arr.push({"id": teacher.plan_short, "display_name": display_name});
        }
    }

    function gen_room_arr(grouped_rooms) {
        room_arr = [];
        for (let room_group of grouped_rooms) {
            let converted_rooms = [];
            for(let room of room_group[1]) {
                converted_rooms.push({"id": room, "display_name": room});
            }
            room_arr.push([room_group[0], converted_rooms]);
        }
    }

    function gen_revision_arr(all_revisions) {
        revision_arr = [];
        for(const [index, revision] of Object.entries(all_revisions)) {
            if (index == 1) {continue;}
            revision_arr.push({
                "id": revision,
                "display_name": format_revision_date(revision, all_revisions[1])
            });
        }
    }

    function getDateDisabled(date) {
        return !enabled_dates.includes(`${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}`);
    }

    function logout() {
        close_modal();
        localStorage.clear();
        clear_plan_cache();

        localStorage.setItem('logged_in', `${$logged_in}`);
        init_vars();
    }

    function reset_selects(plan_type) {
        (plan_type !== "forms") && (selected_form = null);
        (plan_type !== "teachers") && (selected_teacher = null);
        (plan_type !== "rooms") && (selected_room = null);
    }

    function refresh_plan_vars() {
        let tmp_variables = location.hash.split("|");
        if (tmp_variables.length >= 3) {
            school_num = decodeURI(tmp_variables[1]);
            date = decodeURI(tmp_variables[2]);
            plan_type = null;
            plan_value = null;
        }
        if (tmp_variables.length === 5) {
            plan_type = decodeURI(tmp_variables[3]);
            plan_value = decodeURI(tmp_variables[4]);
        }
    }

    function select_plan(favorites, selected_favorite) {
        // check if selected_favorite is in favorites (selected_favorite is the index)
        if (selected_favorite !== -1 && favorites[selected_favorite]) {
            selected_favorite = favorites[selected_favorite];
            school_num = selected_favorite.school_num;
            localStorage.setItem('school_num', school_num);
            plan_type = selected_favorite.plan_type;
            plan_value = selected_favorite.plan_value;
            selected_form = null;
            selected_teacher = null;
            selected_room = null;
            scrollTo(document.getElementsByClassName("plan")[0]);
        }
    }

    function navigate_favorite() {
        if(!load_favorite || !$settings.load_first_favorite) {
            return;
        }
        navigate_page('plan');
        if($favorites.length === 0) {
            return;
        }
        $selected_favorite = 0;
        load_favorite = false;
    }

    function reset_favorite() {
        selected_favorite.set(-1);
    }
    // reset favorite when selecting new plan
    $: (selected_form || selected_teacher || selected_room) && reset_favorite();
    $: if ($selected_favorite !== -1) {
        // check if selected_favorite is in favorites
        if ($favorites.length <= $selected_favorite) {
            selected_favorite.set(-1);
        }
    }

    $logged_in = localStorage.getItem('logged_in') === 'true';
    init_vars();
    check_login_status();
    refresh_plan_vars();

    $: $logged_in && init_indexed_db();
    $: !$logged_in && logout();
    $: select_plan($favorites, $selected_favorite);
    $: school_num && (api_base = `/api/v69.420/${school_num}`);
    $: school_num && get_meta(school_num);
    $: all_revisions = [".newest"].concat((meta?.dates || {})[date] || []);
    //$: school_num && get_preferences();
    $: all_rooms && (grouped_rooms = group_rooms(all_rooms));
    $: $logged_in && (get_settings(), get_favorites(navigate_favorite));
    $: ($settings && Object.keys($settings).length !== 0) && localStorage.setItem("settings", `${JSON.stringify($settings)}`);
    $: update_colors($settings);
    $: $logged_in && get_greeting();

    $: selected_form && set_plan("forms", selected_form);
    $: gen_form_arr(grouped_forms);
    $: selected_teacher && set_plan("teachers", selected_teacher);
    $: gen_teacher_arr(teacher_dict);
    $: selected_room && set_plan("rooms", selected_room);
    $: gen_room_arr(grouped_rooms);
    $: gen_revision_arr(all_revisions);
    $: reset_selects(plan_type);

    const resizeObserver = new ResizeObserver((entries) => {
        footer_padding = entries[0].target.scrollHeight > entries[0].target.clientHeight
    });
    resizeObserver.observe(document.documentElement);

    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        $pwa_prompt = e;
    });

    window.addEventListener('popstate', (e) => {
        let new_location = location.hash.slice(1);
        if((new_location === "login" || new_location === "register") && $logged_in) {
            e.preventDefault();
            history.go(1);
            return;
        }
        navigate_page(new_location);
        if (new_location.startsWith("plan")) {
            refresh_plan_vars();
        }
    });

    let new_location = location.hash.slice(1);
    if(!((new_location === "login" || new_location === "register") && $logged_in)) {
        if(new_location === "favorite") {
            load_favorite = true;
            new_location = "plan";
        }
        navigate_page(new_location);
    }
</script>

<svelte:head>
   <title>Better VPlan{$title ? ` - ${$title}` : ""}</title>
</svelte:head>

{#if $logged_in}
    <Navbar />
{:else if $current_page !== "login" && $current_page !== "register"}
    <LandingPageNavbar />
{/if}

{#if $current_page === ""}
    <FancyBackground />
{/if}

<Settings />
<Changelog />

<div id="page-container">
    <main>
        {#if $current_page === "contact"}
            <Contact />
        {:else if $current_page === "about_us"}
            <AboutUs />
        {:else if $current_page === "impressum"}
            <Impressum />
        {:else if $current_page === ""}
            <LandingPage></LandingPage>
        {:else if $logged_in}
            <!-- !!! Update NotFound protected_routes when adding a new route !!! -->
            {#if $current_page.substring(0, 4) === "plan" || $current_page.substring(0, 8) === "weekplan"}
                <h1 class="responsive-heading">{emoji} {greeting}</h1>
                <!-- {#if $selected_favorite !== -1 && $favorites[$selected_favorite]}
                    Gewählter Favorit: {$favorites[$selected_favorite].name}
                    <br>
                {/if} -->
                <div class="controls-wrapper">
                    <!-- Datepicker -->
                    <div class="control" id="c1">
                        <SveltyPicker
                            format="yyyy-mm-dd"
                            displayFormat="dd.mm.yyyy"
                            disableDatesFn={getDateDisabled}
                            i18n={de}
                            clearBtn={false}
                            todayBtn={false}
                            inputClasses="datepicker-input"
                            bind:value={date}
                        />
                        {#if available_plan_version}
                            <div class="plan-status" transition:fade|local={{duration: 200}}>
                                <span class="material-symbols-outlined" data-plan-type={available_plan_version}>check_circle</span>
                                <span class="status-label">{available_plan_version_map[available_plan_version]}</span>
                            </div>
                        {/if}
                    </div>
                    <!-- Select Form -->
                    <div class="control" id="c2">
                        <Select data={form_arr} grouped={true} bind:selected_id={selected_form} data_name="Klassen">Klasse auswählen</Select>
                    </div>
                    <!-- Select Teacher -->
                    <div class="control" id="c3">
                        <Select data={teacher_arr} bind:selected_id={selected_teacher} data_name="Lehrer">Lehrer auswählen</Select>
                    </div>
                    <!-- Select Room -->
                    <div class="control" id="c4">
                        <Select data={room_arr} grouped={true} bind:selected_id={selected_room} data_name="Räume">Raum auswählen</Select>
                    </div>
                    <!-- Show room overview -->
                    <div class="control" id="c5">
                        <Button on:click={() => {
                            //set_plan("room_overview", "");
                            reset_favorite();
                            // console.log("going to room overview");
                            plan_type = "room_overview";
                            plan_value = "";
                        }}>Freie Räume</Button>
                    </div>
                </div>
                {#if $current_page.substring(0, 4) === "plan"}
                    <Plan bind:api_base bind:school_num bind:date bind:plan_type bind:plan_value bind:all_rooms bind:meta bind:selected_revision bind:enabled_dates bind:available_plan_version external_times={$settings.external_times} />
                {:else}
                    <Weekplan bind:api_base bind:week_start={date} bind:plan_type bind:plan_value />
                {/if}
                <!-- Select Revision (Plan Version) -->
                {#if $settings.show_revision_selector}
                <Select data={revision_arr} bind:selected_id={selected_revision} data_name="Revisions">Zeitstempel des Planuploads auswählen</Select>
                {/if}
            {:else if $current_page === "school_manager"}
                <SchoolManager bind:school_num bind:date bind:plan_type bind:plan_value />
            {:else if $current_page === "favorite"}
                <div style="display: flex; flex-direction: column; gap: 2rem; width: auto; min-height: 50vh; justify-content: center; align-items: center;">
                    <div class="rotating"><span class="material-symbols-outlined fancy-text" style="font-size: max(3rem, 5vw)">sync</span></div>
                    <span class="responsive-text" style="text-align: center;">Lade deine Favoriten...</span>
                </div>
            {:else if $current_page === "favorites"}
                <Favorites />
            {:else if $current_page === "pwa_install"}
                <PwaInstallHelper />
            {:else if $current_page === "stats"}
                <Stats />
            {:else}
                <NotFound />
            {/if}
        {:else if $current_page === "login" || $current_page === "register"}
            <Authentication></Authentication>
        {:else}
            <NotFound />
        {/if}
    </main>
    <Toast />
</div>
<footer class:padding={footer_padding}>
    <Dropdown let:toggle small={true} transform_origin_x="100%" flipped={true}>
        <button slot="toggle_button" on:click={toggle}><span class="material-symbols-outlined">menu</span></button>

        {#if !$logged_in}<button on:click={() => {navigate_page("login")}}>Login</button>{/if}
        <button on:click={() => {navigate_page("")}}>Startseite</button>
        <button on:click={() => {navigate_page("impressum")}}>Impressum</button>
        <button on:click={() => {navigate_page("contact")}}>Kontakt</button>
        <button on:click={() => {navigate_page("about_us")}}>Über Uns</button>
        <button on:click={() => {navigate_page("pwa_install")}}>Installieren</button>
    </Dropdown>
</footer>

<style lang="scss">
  .rotating {
    animation: rotate 2s linear infinite;
  }

  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(-360deg);
    }
  }

  .fancy-text {
    background: linear-gradient(310deg, #cc33ff, #3358ff, #33bbff);
    color: transparent;
    -webkit-background-clip: text;
    background-clip: text;
    background-size: 600% 600%;

    -webkit-animation: colorScroll 3s ease infinite;
    -moz-animation: colorScroll 3s ease infinite;
    animation: colorScroll 3s ease infinite;
  }

  @-webkit-keyframes colorScroll {
    0% {
      background-position: 0 50%
    }
    50% {
      background-position: 100% 50%
    }
    100% {
      background-position: 0 50%
    }
  }

  @-moz-keyframes colorScroll {
    0% {
      background-position: 0 50%
    }
    50% {
      background-position: 100% 50%
    }
    100% {
      background-position: 0 50%
    }
  }

  @keyframes colorScroll {
    0% {
      background-position: 0 50%
    }
    50% {
      background-position: 100% 50%
    }
    100% {
      background-position: 0 50%
    }
  }

  .plan-status {
    pointer-events: none;
    position: absolute;
    top: 0;
    left: 15px;
    bottom: 0;
    width: min(30%, 175px) !important;
    display: flex;
    gap: 5px;
    flex-direction: row;
    justify-content: flex-start;
    align-items: center;

    .material-symbols-outlined {
      font-size: var(--font-size-md);
      transition: all .2s ease;

      &[data-plan-type=cached] {
        color: rgba(255, 255, 255, 0.5);
      }

      &[data-plan-type=network_cached] {
        color: #00db00;
      }

      &[data-plan-type=network_uncached] {
        color: #dbae00;
      }
    }

    .status-label {
      font-size: var(--font-size-sm);
      color: rgba(255, 255, 255, 0.5);
      hyphens: auto;
      text-align: left;
    }
  }

  #page-container {
    max-width: 100%;
    overflow-x: hidden;
    position: relative;
    min-height: calc(100vh - 56px);
    padding-bottom: 15px;

    @media only screen and (min-width: 602px) {
      min-height: calc(100vh - 64px);
    }
  }

  footer {
    float: right;
    height: calc(var(--font-size-sm) * 2);
    width: calc(var(--font-size-sm) * 2);
    margin-top: calc(var(--font-size-sm) * -2);
    display: flex;
    background: rgba(0, 0, 0, 0.5);
    align-items: center;
    flex-direction: row;
    justify-content: flex-start;

    &.padding {
      padding-right: 16px;
    }

    button {
      width: 100%;
      height: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
      border: none;
      background: transparent;
      font-size: var(--font-size-sm);
      color: white;

      span {
        font-size: inherit;
      }
    }
  }

  :global(.responsive-heading) {
    font-size: var(--font-size-xl);
    margin-bottom: 15px;
    line-height: 1.2;
    font-weight: 700;
  }

  :global(.responsive-text) {
    font-size: var(--font-size-base);
    line-height: 1.6;
    font-weight: 400;
  }

  .controls-wrapper {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(3, 1fr);
    grid-column-gap: 10px;
    grid-row-gap: 15px;
    margin-bottom: 40px;

    .control {
      & > :global(*) {
        width: 100%;
        height: 100%;
      }

      &#c1 {
        grid-area: 1 / 1 / 2 / 3;
      }

      &#c2 {
        grid-area: 2 / 1 / 3 / 2;
      }

      &#c3 {
        grid-area: 2 / 2 / 3 / 3;
      }

      &#c4 {
        grid-area: 3 / 1 / 4 / 2;
      }

      &#c5 {
        grid-area: 3 / 2 / 4 / 3;
      }

      &#c1 {
        position: relative;
        --sdt-bg-main: var(--background);
        --sdt-shadow-color: var(--background);
        --sdt-wrap-shadow: 0px 0px 6px rgba(0, 0, 0, 0.3);
        --sdt-radius: 5px;
        --sdt-color: var(--text-color);
        --sdt-color-selected: var(--text-color);
        --sdt-header-color: var(--text-color);
        --sdt-primary: var(--accent-color);
        --sdt-disabled-date: var(--cancelled-color);
        --sdt-disabled-date-bg: var(--sdt-bg-main);
        --sdt-btn-bg-hover: rgba(255, 255, 255, 0.2);
        --sdt-btn-header-bg-hover: var(--sdt-btn-bg-hover);
        --sdt-today-indicator: var(--sdt-bg-main);

        :global(.datepicker-input) {
          width: 100%;
          height: 100%;
          border: none;
          border-radius: 5px;
          background-color: rgba(255, 255, 255, 0.2);
          color: var(--text-color);
          font-size: var(--font-size-base);
          text-align: center;
        }

        :global(.std-calendar-wrap) {
          left: 50% !important;
          transform: translateX(-50%);
          border-radius: 5px;
          overflow: hidden;
        }

        :global(.is-selected) {
          pointer-events: none;
        }

        :global(.std-calendar-wrap::before) {
          content: "";
          position: absolute;
          inset: 0;
          background: rgba(255, 255, 255, 0.05);
        }
      }
    }

    @media only screen and (min-width: 1501px) {
      grid-template-columns: repeat(4, 1fr);
      grid-template-rows: repeat(2, 1fr);

      .control {
        &#c1 {
          grid-area: 1 / 1 / 2 / 5;
        }

        &#c2 {
          grid-area: 2 / 1 / 3 / 2;
        }

        &#c3 {
          grid-area: 2 / 2 / 3 / 3;
        }

        &#c4 {
          grid-area: 2 / 3 / 3 / 4;
        }

        &#c5 {
          grid-area: 2 / 4 / 3 / 5;
        }
      }
    }
  }

  main {
    padding-top: 25px;
    margin: 64px auto;
    @media only screen and (max-width: 601px) {
      margin: 56px auto;
    }
    margin-bottom: 0px !important;

    max-width: 1280px;
    width: 90%;
    @media only screen and (min-width: 601px) {
      width: 85%;
    }
    @media only screen and (min-width: 993px) {
      width: 70%;
    }
    @media only screen and (max-width: 500px) {
      width: 95%;
    }
  }

  :global {
    ul, ol {
      padding-left: 22px !important;
      // padding-left: 40px !important;
      // @media only screen and (max-width: 1501px) {
      //     padding-left: 22px !important;
      // }
      list-style-type: disc !important;
    }
  }
</style>