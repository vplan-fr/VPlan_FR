<script>
    import Plan from "./Plan.svelte";
    import Weekplan from "./Weekplan.svelte";
    import Authentication from "./Authentication.svelte";
	import Toast from './Components/Toast.svelte';
    import Navbar from "./Navbar.svelte";
    import Settings from "./Settings.svelte";
    import AboutUs from "./AboutUs.svelte";
    import SveltyPicker from 'svelty-picker';
    import {get_settings, group_rooms, update_colors, analyze_local_storage, navigate_page} from "./utils.js";
    import {notifications} from './notifications.js';
    import {logged_in, title, current_page, preferences, settings, active_modal, pwa_prompt} from './stores.js'
    import {customFetch, clear_caches, format_revision_date} from "./utils.js";
    import SchoolManager from "./SchoolManager.svelte";
    import Preferences from "./Preferences.svelte";
    import Changelog from "./Changelog.svelte";
    import Select from "./Components/Select.svelte";
    import Contact from "./Contact.svelte";
    import Impressum from "./Impressum.svelte";
    import { de } from 'svelty-picker/i18n';
    import { onMount } from "svelte";
    import PwaInstallHelper from "./PWAInstallHelper.svelte";
    import Dropdown from "./Components/Dropdown.svelte";
    import { animateScroll } from 'svelte-scrollto-element';
    import Button from "./Components/Button.svelte";

    let school_num = localStorage.getItem('school_num');
    let date = null;
    let all_revisions = [".newest"];
    let plan_type;
    let plan_value;
    let teacher_list = [];
    let all_rooms;
    let grouped_forms = [];
    let api_base;


    $: api_base = `/api/v69.420/${school_num}`;
    $logged_in = localStorage.getItem('logged_in') === 'true';
    check_login_status();
    clear_caches();

    const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s);

    let selected_teacher;
    let selected_room;
    let selected_form;
    let selected_revision = ".newest";
    let meta = {};
    let all_meta = {};
    let enabled_dates = [];
    let grouped_rooms = [];
    let course_lists = {};
    let footer_padding = false;

    const resizeObserver = new ResizeObserver((entries) => {
        footer_padding = entries[0].target.scrollHeight > entries[0].target.clientHeight
    });
    resizeObserver.observe(document.documentElement);

    $: if (all_rooms) {
        grouped_rooms = group_rooms(all_rooms);
    }

    function get_meta(api_base) {
        if (!$logged_in || !school_num) {
            return;
        }
        if (school_num === null || school_num === "") {
            return;
        }
        let data_from_cache = false;
        let data = localStorage.getItem(`${school_num}_meta`);
        if (data !== "undefined" && data) {
            data = JSON.parse(data);
            all_meta = data;
            meta = data.meta;
            all_rooms = data.rooms;
            teacher_list = Object.keys(data.teachers);
            grouped_forms = data.forms.grouped_forms;
            enabled_dates = Object.keys(data.dates);
            date = data.date;
            course_lists = data.forms.forms;
            data_from_cache = true;
        }
        customFetch(`${api_base}/meta`)
            .then(data => {
                // console.log("Meta geladen");
                try {
                    localStorage.setItem(`${school_num}_meta`, JSON.stringify(data));
                } catch (error) {
                    if (error.name === 'QuotaExceededError' ) {
                        notifications.danger("Die Schulmetadaten konnten nicht gecached werden.")
                    } else {
                        throw error;
                    }
                }
                all_meta = data;
                meta = data.meta;
                all_rooms = data.rooms;
                teacher_list = Object.keys(data.teachers);
                grouped_forms = data.forms.grouped_forms;
                enabled_dates = Object.keys(data.dates);
                date = data.date;
                course_lists = data.forms.forms;
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
                $logged_in = data["logged_in"];
                localStorage.setItem('logged_in', `${$logged_in}`);
            })
            .catch(error => {
                //notifications.danger(error);
                console.error("Login-Status konnte nicht überprüft werden");
            }
        );
    }

    function get_preferences() {
        customFetch(`${api_base}/preferences`)
            .then(data => {
                preferences.set(data);
            })
            .catch(error => {
                console.error("Preferences konnten nicht geladen werden.");
            })
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
        if(curr_day <= 5 && curr_day > 0) {
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
            if(curr_day === 5 || curr_day === 6) {
                emoji = choose(["🕺", "💃", "🎮", "🎧"]);
            }
        }
        return emoji;
    }

    let emoji = get_emoji();
    let greeting = "";
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
        var headerOffset = window.innerWidth > 601 ? 74 : 66;

        animateScroll.scrollTo({element: element, offset: headerOffset, duration: 200});
    }

    function set_plan(new_plan_type, new_plan_value) {
        plan_type = new_plan_type;
        plan_value = new_plan_value;
        scrollTo(document.getElementsByClassName("plan-heading")[0]);
    }

    let form_arr = [];
    let teacher_arr = [];
    let room_arr = [];
    let revision_arr = [];

    function gen_form_arr(grouped_forms) {
        form_arr = [];
        for (const [form_group, forms] of Object.entries(grouped_forms)) {
            let converted_forms = [];
            for(let form of forms) {
                converted_forms.push({"id": form, "display_name": form});
            }
            form_arr.push([form_group, converted_forms]);
        }
    }

    function gen_teacher_arr(teacher_list) {
        teacher_arr = [];
        for(let teacher of teacher_list) {
            teacher_arr.push({"id": teacher, "display_name": teacher});
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
            if(index == 1) {continue;}
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
        school_num = null;
        localStorage.clear();
        localStorage.setItem('logged_in', `${$logged_in}`);
    }

    function reset_plan_vars() {
        date = null;
        plan_type = null;
        plan_value = null;
    }

    function reset_selects() {
        ("forms" !== plan_type) && (selected_form = null);
        ("teachers" !== plan_type) && (selected_teacher = null);
        ("rooms" !== plan_type) && (selected_room = null);
    }

    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        $pwa_prompt = e;
    });

    $: school_num, reset_plan_vars();
    $: $logged_in && get_settings();
    $: localStorage.setItem("settings", `${JSON.stringify($settings)}`)
    $: $logged_in && get_meta(api_base);
    $: all_revisions = [".newest"].concat((all_meta?.dates || {})[date] || []);
    $: $logged_in && get_greeting();
    $: !$logged_in && logout();
    $: !$logged_in && close_modal();
    $: school_num, $logged_in && get_preferences();
    $: update_colors($settings);
    $: selected_form && set_plan("forms", selected_form);
    $: gen_form_arr(grouped_forms);
    $: selected_teacher && set_plan("teachers", selected_teacher);
    $: gen_teacher_arr(teacher_list);
    $: selected_room && set_plan("rooms", selected_room);
    $: gen_room_arr(grouped_rooms);
    $: gen_revision_arr(all_revisions);
    $: plan_type, reset_selects();

    onMount(() => {
        // console.log("Mounted App.svelte");
    });

    window.addEventListener('popstate', (e) => {
        let new_location = location.hash.slice(1);
        if((new_location === "login" || new_location === "register") && $logged_in) {
            e.preventDefault();
            history.go(1);
            return;
        }
        if(new_location === "") {new_location = "plan";}
        navigate_page(new_location);
    });

    let new_location = location.hash.slice(1);
    if(!((new_location === "login" || new_location === "register") && $logged_in)) {
        if(new_location === "") {new_location = "plan";}
        navigate_page(new_location);
    }

    //analyze_local_storage();
</script>

<svelte:head>
   <title>Better VPlan{$title ? ` - ${$title}` : ""}</title>
</svelte:head>

{#if $logged_in}
    <Navbar />
{/if}

<Settings />
<Changelog />
<Preferences bind:api_base bind:grouped_forms bind:course_lists bind:school_num />

<div id="page-container">
    <main>
        {#if $current_page === "contact"}
            <Contact />
        {:else if $current_page === "about_us"}
            <AboutUs />
        {:else if $current_page === "impressum"}
            <Impressum />
        {:else if $logged_in}
            {#if $current_page.substring(0, 4) === "plan" || $current_page === "weekplan"}
                <h1 class="responsive-heading">{emoji} {greeting}</h1>
                <div class="controls-wrapper">
                    <!-- Datepicker -->
                    <div class="control" id="c1">
                        <SveltyPicker
                            format="yyyy-mm-dd"
                            displayFormat="dd.mm.yyyy"
                            disableDatesFn={getDateDisabled}
                            initialDate={(date === null) ? new Date() : new Date(date)}
                            i18n={de}
                            clearBtn={false}
                            todayBtn={false}
                            inputClasses="datepicker-input"
                            bind:value={date}
                        />
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
                            set_plan("room_overview", "");
                        }}>Raumübersicht</Button>
                    </div>
                </div>
                {#if $current_page.substring(0, 4) === "plan"}
                    <Plan bind:api_base bind:school_num bind:date bind:plan_type bind:plan_value bind:all_rooms bind:all_meta bind:selected_revision bind:enabled_dates external_times={$settings.external_times} />
                {:else}
                    <Weekplan bind:api_base bind:week_start={date} bind:plan_type bind:plan_value />
                {/if}
                <!-- Select Revision (Plan Version) -->
                {#if $settings.show_revision_selector}
                <Select data={revision_arr} bind:selected_id={selected_revision} data_name="Revisions">Zeitstempel des Planuploads auswählen</Select>
                {/if}
            {:else if $current_page === "school_manager"}
                <SchoolManager bind:school_num />
            {:else if $current_page === "pwa_install"}
                <PwaInstallHelper />
            {:else}
                <span class="responsive-text">Seite nicht gefunden!</span>
            {/if}
        {:else}
            <Authentication></Authentication>
        {/if}
    </main>
    <Toast />
</div>
<footer class:padding={footer_padding}>
    <Dropdown let:toggle small={true} transform_origin_x="100%" flipped={true}>
        <button slot="toggle_button" on:click={toggle}><span class="material-symbols-outlined">menu</span></button>
        
        <button on:click={() => {navigate_page("impressum")}}>Impressum</button>
        <button on:click={() => {navigate_page("contact")}}>Kontakt</button>
        <button on:click={() => {navigate_page("about_us")}}>Über Uns</button>
        {#if !$logged_in}<button on:click={() => {navigate_page("login")}}>Login</button>{/if}
    </Dropdown>
</footer>

<style lang="scss">
    #page-container {
        position: relative;
        min-height: calc(100vh - 56px);

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
        line-height: 1.6;
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
        grid-row-gap: 10px;
        margin-bottom: 40px;

        .control {
            & > :global(*) {
                width: 100%;
                height: 100%;
            }

            &#c1 {grid-area: 1 / 1 / 2 / 3;}
            &#c2 {grid-area: 2 / 1 / 3 / 2;}
            &#c3 {grid-area: 2 / 2 / 3 / 3;}
            &#c4 {grid-area: 3 / 1 / 4 / 2;}
            &#c5 {grid-area: 3 / 2 / 4 / 3;}

            &#c1 {
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
                --sdt-color-selected: var(--text-color);
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
                &#c1 {grid-area: 1 / 1 / 2 / 5;}
                &#c2 {grid-area: 2 / 1 / 3 / 2;}
                &#c3 {grid-area: 2 / 2 / 3 / 3;}
                &#c4 {grid-area: 2 / 3 / 3 / 4;}
                &#c5 {grid-area: 2 / 4 / 3 / 5;}
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
            padding-left: 40px !important;
            @media only screen and (max-width: 1501px) {
                padding-left: 22px !important;
            }
            list-style-type: disc !important;
        }
    }
</style>