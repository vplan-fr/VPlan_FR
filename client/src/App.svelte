<script>
    import Plan from "./Plan.svelte";
    import Weekplan from "./Weekplan.svelte";
    import Authentication from "./Authentication.svelte";
	import Toast from './Components/Toast.svelte';
    import Navbar from "./Navbar.svelte";
    import Settings from "./Settings.svelte";
    import AboutUs from "./AboutUs.svelte";
    import {DatePicker} from 'attractions';
    import {get_settings, group_rooms, update_colors} from "./utils.js";
    import {notifications} from './notifications.js';
    import {logged_in, title, current_page, preferences, settings, active_modal} from './stores.js'
    import {customFetch, clear_caches} from "./utils.js";
    import SchoolManager from "./SchoolManager.svelte";
    import Preferences from "./Preferences.svelte";
    import Changelog from "./Changelog.svelte";

    let school_num = localStorage.getItem('school_num');
    let date = null;
    let plan_type = "forms";
    let plan_value = "JG12";
    let teacher_list = [];
    let all_rooms;
    let grouped_forms = [];
    let api_base;
    
    $: api_base = `/api/v69.420/${school_num}`;
    $logged_in = localStorage.getItem('logged_in') === 'true';
    check_login_status();
    clear_caches();
    
    if ($logged_in) {
        get_settings();
    }

    const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s);

    let selected_teacher;
    let selected_room;
    let selected_form;
    let meta = {};
    let all_meta = {};
    let disabledDates = [];
    let enabled_dates = [];
    let grouped_rooms = [];
    let course_lists = {};

    $: if (all_rooms) {
        grouped_rooms = group_rooms(all_rooms);
    }

    function get_meta(api_base) {
        if (!$logged_in) {
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
                    notifications.info("Metadaten aus Cache geladen", 2000);
                } else {
                    notifications.danger(error);
                }
            });
    }

    function update_disabled_dates(enabled_dates) {
        if (!$logged_in) {
            return;
        }
        let tmp_start = new Date(enabled_dates[enabled_dates.length - 1]);
        let tmp_end = new Date(enabled_dates[0]);
        tmp_start.setDate(tmp_start.getDate() + 1);
        tmp_end.setDate(tmp_end.getDate() - 1);
        disabledDates = [
            {start: new Date("0"), end: tmp_end},
            {start: tmp_start, end: new Date("9999")},
        ];
        for (let i = 0; i < enabled_dates.length; i++) {
            tmp_start = new Date(enabled_dates[i]);
            tmp_end = new Date(enabled_dates[i + 1]);
            tmp_start.setDate(tmp_start.getDate() + 1);
            tmp_end.setDate(tmp_end.getDate() - 1);
            disabledDates.push({
                start: tmp_start,
                end: tmp_end
            });
        }
    }

    function check_login_status() {
        customFetch('/auth/check_login')
            .then(data => {
                $logged_in = data["logged_in"];
                localStorage.setItem('logged_in', `${$logged_in}`);
            })
            .catch(error => {
                //notifications.danger(error);
                notifications.danger("Login-Status konnte nicht überprüft werden");
            }
        );
    }

    function get_preferences() {
        customFetch(`${api_base}/preferences`)
            .then(data => {
                preferences.set(data);
            })
            .catch(error => {
                notifications.danger(error)
            })
    }

    let greeting = "";
    function get_greeting() {
        customFetch("/auth/greeting")
            .then(data => {
                let curr_date = new Date();
                let curr_hours = curr_date.getHours();
                let emoji = "👋";
                if (curr_hours >= 4 && curr_hours < 8) {
                    emoji = "🥱";
                }
                if (curr_hours >= 18 || curr_hours < 4) {
                    emoji = "😴";
                }
                greeting = `${emoji} ${data}`;
            })
            .catch(error => {
                notifications.danger(error);
            })
    }

    function close_modal() {
        $active_modal = "";
    }

    $: $logged_in && get_settings();
    $: $logged_in && get_meta(api_base);
    $: $logged_in && update_disabled_dates(enabled_dates);
    $: $logged_in && get_greeting();
    $: !$logged_in && close_modal();
    $: school_num, $logged_in && get_preferences();
    $: update_colors($settings);
</script>

<svelte:head>
   <title>Better VPlan{$title ? ` - ${$title}` : ""}</title>
</svelte:head>

{#if $logged_in}
    <Navbar />
{/if}

<Settings />

<main>
    {#if $logged_in}
        {#if $current_page.substring(0, 4) === "plan" || $current_page === "weekplan"}
            <Changelog></Changelog>
            <h1 class="responsive-heading">{greeting}</h1>
            <div class="controls-wrapper">
                <div class="control" id="c1">
                    <DatePicker
                        format="%Y-%m-%d"
                        locale="de-DE"
                        closeOnSelection
                        bind:disabledDates
                        value={(date === null) ? null : new Date(date)}
                        on:change={(evt) => {
                            let tmp_dat = evt.detail.value;
                            date = `${tmp_dat.getFullYear()}-${pad(tmp_dat.getMonth()+1)}-${pad(tmp_dat.getDate())}`;
                        }}
                    />
                </div>
                <div class="control" id="c2">
                    <div class="input-field">
                        <select bind:value={selected_form}
                            on:change={() => {plan_type = 'forms'; plan_value = selected_form}}>
                            {#each Object.entries(grouped_forms) as [form_group, forms]}
                                <optgroup label={form_group}>
                                    {#each forms as form}
                                        <option value="{form}">{form}</option>
                                    {/each}
                                </optgroup>
                            {/each}
                        </select>
                    </div>
                </div>
                <div class="control" id="c3">
                    <div class="input-field">
                        <select bind:value={selected_teacher}
                            on:change={() => {plan_type = 'teachers'; plan_value = selected_teacher}}>
                            {#each teacher_list as teacher}
                                <option value={teacher}>{teacher}</option>
                            {/each}
                        </select>
                    </div>
                </div>
                <div class="control" id="c4">
                    <div class="input-field">
                        <select bind:value={selected_room}
                            on:change={() => {plan_type = 'rooms'; plan_value = selected_room}}>
                            {#each grouped_rooms as [category, rooms]}
                                <optgroup label={category}>
                                    {#each rooms as room}
                                        <option value="{room}">{room}</option>
                                    {/each}
                                </optgroup>
                            {/each}
                        </select>
                    </div>
                </div>
                <div class="control" id="c5">
                    <button class="button" on:click={() => {
                        plan_type = "free_rooms";
                        plan_value = "";
                    }}>Raumübersicht</button>
                </div>
            </div>
            {#if $current_page.substring(0, 4) === "plan"}
                <Plan bind:api_base bind:school_num bind:date bind:plan_type bind:plan_value bind:all_rooms bind:all_meta/>
            {:else}
                <Weekplan bind:api_base bind:week_start={date} bind:plan_type bind:plan_value />
            {/if}
        {:else if $current_page === "school_manager"}
            <SchoolManager bind:school_num />
        {:else if $current_page === "about_us"}
            <AboutUs />
        {:else if $current_page === "preferences"}
            <Preferences bind:api_base bind:grouped_forms bind:course_lists bind:school_num />
        {:else}
            <span>Seite nicht gefunden!</span>
        {/if}
    {:else}
        <Authentication></Authentication>
    {/if}
</main>
<Toast />

<style lang="scss">
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
        margin-bottom: 20px;

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

    .button {
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        border: none;
        background-color: rgba(255, 255, 255, 0.2);
        color: var(--text-color);
        border-radius: 5px;
        padding: .5em;
        margin: 3px;
        font-size: var(--font-size-base);
        position: relative;

        &.btn-small {
            font-size: var(--font-size-sm);
        }

        .material-symbols-outlined {
            font-size: 1.3em;
            float: right;
            margin-left: .2em;
        }
    }

    main {
        padding-top: 25px;
        margin: 64px auto;
        @media only screen and (max-width: 601px) {
            margin: 56px auto;
        }

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
        ul {
            padding-left: 40px !important;
            @media only screen and (max-width: 1501px) {
                padding-left: 22px !important;
            }
            list-style-type: disc !important;
        }
    }
</style>