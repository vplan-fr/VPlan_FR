<script>
    import {onMount} from 'svelte';
    import Lesson from './Lesson.svelte';
    import Rooms from "../Rooms.svelte";
    import { swipe } from 'svelte-gestures';
    import {indexed_db, settings, title, selected_favorite, favorites, api_base} from '../../stores.js';
    import {arraysEqual, format_date, format_timestamp, replace_hash, replace_page, update_hash} from "../../utils.js";
    import {sameBlock, get_plan_version, get_teacher_data, load_plan, gen_location_hash, load_lessons, apply_preferences, getDateDisabled} from "../../plan.js";
    import {getLabelOfPeriods} from "../../periods_utils.js";
    import DayInfos from "./DayInfos.svelte";

    export let school_num;
    export let date;
    export let plan_type;
    export let plan_value;
    export let meta;
    export let extra_height = true;
    export let week_letter = "";
    export let external_times = true;
    export let all_rooms;
    export let revision_arr;
    export let enabled_dates;
    export let free_days;
    export let block_config;
    export let available_plan_version;
    let used_rooms_hidden = true;
    let selected_revision = ".newest";

    const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s);
    let plan_data = [];
    let all_lessons = [];
    let rooms_data = {};
    let info;
    let exams;
    let last_fetch;
    let is_default_plan = false;
    let loading = false;
    let loading_failed = false;
    let cache_loading_failed = false;
    let network_loading_failed = false;
    let data_from_cache = false;
    const plan_type_map = {
        "forms": "Klasse",
        "rooms": "Raum",
        "teachers": "Lehrer"
    };
    let controller = new AbortController();
    let full_teacher_name = null;
    let teacher_contact_link = null;
    let teacher_image_path = null;
    let preferences_apply = true;
    let lessons = [];
    let show_left_key = true;
    let left_key_default_plan = false;
    let show_right_key = true;
    let right_key_default_plan = false;
    let last_updated = {};
    let caching_successful;

    // === Handlers + Callbacks ===

    function reset_plan_vars() {
        all_lessons = [];
        rooms_data = null;
        plan_type = null;
        plan_value = null;
    }

    function update_lessons(type, data) {
        if(type === "rooms_data") {
            rooms_data = data;
        } else if(type === "all_lessons") {
            all_lessons = data;
        } else {
            console.error(`lesson_updater: unknown type "${type}"`);
        }
    }

    function handle_plan_data(data) {
        plan_data = data;
        info = data.info;
        last_fetch = data.last_fetch ?? '1970-01-01';
        is_default_plan = data.is_default_plan;
        exams = data.exams;
        week_letter = info.week;
    }

    function handle_loading_state(loading_type, state) {
        switch(loading_type) {
            case 'loading':
                loading = state;
                break;
            case 'data_from_cache':
                data_from_cache = state;
                break;
            case 'cache_loading_failed':
                cache_loading_failed = state;
                break;
            case 'network_loading_failed':
                network_loading_failed = state;
                break;
            case 'caching_successful':
                caching_successful = state;
                break;
            default:
                console.error("Unsupported loading_type: " + loading_type);
                break;
        }
    }

    function renew_abort_controller() {
        controller.abort();
        controller = new AbortController();
        return controller;
    }

    function get_valid_date(date, direction) {
        let tmp_date;
        let date_index = enabled_dates.indexOf(date);
        if(date_index !== -1 && enabled_dates.length > date_index+direction) {
            tmp_date = enabled_dates[date_index+direction];
        } else {
            // Removed due to being more annoying than it bringing value to the UX
            // notifications.danger("Für dieses Datum existiert kein Vertretungsplan!");
            tmp_date = new Date(date);
            tmp_date.setDate(tmp_date.getDate() + direction);
            let tmp_str_date = `${tmp_date.getFullYear()}-${pad(tmp_date.getMonth()+1)}-${pad(tmp_date.getDate())}`;
            let tmp_disabled = getDateDisabled(enabled_dates, free_days, tmp_str_date);
            while (tmp_disabled) {
                tmp_date.setDate(tmp_date.getDate() + direction);
                tmp_str_date = `${tmp_date.getFullYear()}-${pad(tmp_date.getMonth()+1)}-${pad(tmp_date.getDate())}`;
                // If Date is before first enabled_date, return
                if (tmp_str_date < enabled_dates[0]) {return;}
                tmp_disabled = getDateDisabled(enabled_dates, free_days, tmp_str_date);
            }
            tmp_date = tmp_str_date;
        }
        return tmp_date;
    }

    function change_day(direction) {
        let tmp_valid_date = get_valid_date(date, direction);
        if(tmp_valid_date) {date = tmp_valid_date}
    }

    function keydown_handler(event) {
        if($settings.day_switch_keys) {
            if(event.key === "ArrowLeft") {
                event.preventDefault();
                change_day(-1);
            } else if(event.key === "ArrowRight") {
                event.preventDefault();
                change_day(1);
            }
        }
    }

    function swipe_handler(event) {
        if($settings.swipe_day_change) {
            if(event.detail.direction === "right") {
                change_day(-1);
            } else if(event.detail.direction === "left") {
                change_day(1);
            }
        }
    }

    function update_date_btns() {
        let valid_prev_date = get_valid_date(date, -1);
        left_key_default_plan = valid_prev_date && enabled_dates.indexOf(valid_prev_date) === -1;
        show_left_key = !!valid_prev_date;
        right_key_default_plan = enabled_dates.indexOf(date) === -1 || enabled_dates.indexOf(date) === enabled_dates.length - 1;
        show_right_key = true;
    }

    function handle_last_updated(given_date, renew) {
        if(!renew) {
            return last_updated[given_date] || new Date(1970, 1, 1);
        }

        last_updated[given_date] = new Date();
    }

    onMount(() => {
        if(!school_num) {
            replace_page('school_manager');
        }
        title.set("Plan");
    });

    // === Load Plan + Lessons ===
    // Check if new plan has to be loaded and load it
    $: $indexed_db, load_plan(
        $api_base,
        school_num, 
        date, 
        selected_revision, 
        enabled_dates,
        free_days,
        handle_last_updated, handle_loading_state, handle_plan_data, renew_abort_controller
    );
    // Load the new lessons on change to selected plan
    $: meta && load_lessons(plan_data, school_num, plan_type, plan_value, meta, reset_plan_vars, update_lessons);
    // Apply Preferences to lessons
    $: lessons = apply_preferences(plan_type, preferences_apply, $selected_favorite, $favorites, all_lessons);

    // === Load Extra Teacher Data ===
    // Get teacher data (Name, Contact and Image Link)
    $: if(plan_type === "teachers") {
        [full_teacher_name, teacher_contact_link, teacher_image_path] = get_teacher_data(meta.teachers, plan_value, school_num);
    }
    
    // === UI + Navigation ===
    // Update visibility of date switching buttons
    $: date && enabled_dates && update_date_btns();
    
    // Get if loading failed
    $: loading_failed = (cache_loading_failed && network_loading_failed && !loading);
    
    // Get plan version string
    $: available_plan_version = get_plan_version(is_default_plan, data_from_cache, network_loading_failed, caching_successful);
    
    // Update location hash
    $: school_num, date, plan_type, plan_value, (() => {
        if(location.hash === "#plan") {
            replace_hash(gen_location_hash("plan", school_num, date, plan_type, plan_value))
            return;
        }
        update_hash(gen_location_hash("plan", school_num, date, plan_type, plan_value));
    })();
</script>

<svelte:window on:keydown={keydown_handler}/>
<svelte:body use:swipe={{ timeframe: 300, minSwipeDistance: 60, touchAction: 'pan-y' }} on:swipe={swipe_handler} />

<div class:plan={plan_type !== "room_overview"} class:extra-height={extra_height}>
    {#if plan_type !== "room_overview"}
        {#if info && plan_type && plan_value}
            {#if plan_type === "forms" && ($selected_favorite !== -1)}
                <button on:click={() => {preferences_apply = !preferences_apply}} class="plus-btn">{preferences_apply ? "Alle Stunden anzeigen" : "Nur ausgewählte anzeigen"}</button>
            {/if}
            <h1 class="plan-heading">
                <!--Plan für {plan_type_map[plan_type]} <span class="custom-badge">{plan_value}{#if plan_type === "teachers"}{#if full_teacher_name !== null}{` (${full_teacher_name})`}{/if}{#if teacher_image_path !== null}<img class="teacher-img" src="{teacher_image_path}" alt="Lehrer Portrait">{/if}{/if}</span> <span>am</span> <span class="custom-badge">{format_date(date)}</span> <span class="no-linebreak">({info.week}-Woche)</span>-->
                Plan{#if is_default_plan}vorhersage{/if} für {plan_type_map[plan_type]} <span class="custom-badge">{plan_value}{#if plan_type === "teachers"}{#if full_teacher_name !== null}{` (${full_teacher_name})`}{/if}{/if}</span> <span>am</span> <span class="custom-badge">{format_date(date)}</span> <span class="no-linebreak">{#if info.week}({info.week}-Woche){/if}</span>
            </h1>
        {/if}
        {#if loading}
            <span class="responsive-text">Lädt...</span>
        {:else if loading_failed}
            <span class="responsive-text">Plan{#if is_default_plan}vorhersage{/if} konnte nicht geladen werden.</span>
        {:else}
            {#if lessons.length === 0}
            {#if plan_type}    
                <span class="responsive-text">Keine Stunden</span>
            {:else}
                <span class="responsive-text">Wähle eine Klasse, einen Lehrer, einen Raum oder die Raumübersicht aus, um {#if is_default_plan}eine Planvorhersage{:else}einen Plan{/if} zu sehen.</span>
            {/if}
            {:else}
            <div class="lessons-wrapper">
                {#if external_times}
                    <div class="deco-bar"></div>
                {/if}
                {#each lessons as lesson, i}
                    {#if external_times}    
                        {#if !all_lessons[i-1] || (!arraysEqual(lesson.periods, lessons[i-1].periods))}
                            <span class="lesson-time" class:gap={lessons[i-1] && !sameBlock(lesson.periods, lessons[i-1].periods)}>{getLabelOfPeriods(lesson.periods, block_config)}{lesson.begin != null && lesson.end != null ? ": " + lesson.begin + " - " + lesson.end : ""}</span>
                        {/if}
                    {/if}
                    <Lesson lesson={lesson} bind:plan_type bind:plan_value bind:date bind:block_config display_time={!external_times} />
                {/each}
            </div>
            {/if}
        {/if}
    {:else}
        <button on:click={() => {used_rooms_hidden = !used_rooms_hidden}} class="plus-btn">{used_rooms_hidden ? "Besetzte Räume anzeigen" : "Nur freie Räume anzeigen"}</button>
        {#if info}
            <h1 class="plan-heading">Freie Räume am <span class="custom-badge">{format_date(date)}</span> <span class="no-linebreak"/>({info.week}-Woche)</h1>
        {/if}
        {#if loading}
            <span class="responsive-text">Lädt...</span>
        {:else if loading_failed}
            <span class="responsive-text">Plan{#if is_default_plan}vorhersage{/if} konnte nicht geladen werden</span>
        {:else}
            <Rooms rooms_data={rooms_data} bind:plan_type bind:plan_value bind:all_rooms bind:used_rooms_hidden bind:block_config/>
        {/if}
    {/if}
    <DayInfos
        {exams}
        {info}
        {revision_arr}
        {is_default_plan}
        {last_fetch}
        bind:selected_revision
        bind:date
        bind:plan_type
        bind:plan_value
    />
</div>
<div class="day-controls">
    <button tabindex="-1" on:click={() => {change_day(-1);}} class:hidden={!show_left_key} class:is_default_plan={left_key_default_plan}><span class="material-symbols-outlined left">arrow_back_ios_new</span></button>
    <button tabindex="-1" on:click={() => {change_day(1);}} class:hidden={!show_right_key} class:is_default_plan={right_key_default_plan}><span class="material-symbols-outlined right">arrow_forward_ios</span></button>
</div>

<style lang="scss">
    .teacher-img {
        height: 1.5em;
        aspect-ratio: 1;
        object-fit: cover;
        border-radius: 10px;
        box-sizing: border-box;
        padding: .08em 0;
    }

    .dropdown-arrow {
        font-size: 1.4em;
        display: block;
        transition: transform .2s ease;
        pointer-events: none;

        @media only screen and (min-width: 1501px) {
            font-size: 1em;
            margin-left: .2em;
         
            &.centered_txt {
                position: absolute;
                right: 10px;
            }
        }
    }

    :global(.open) .dropdown-arrow {
        transform: rotate(180deg);
    }

    .day-controls {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100vw;
        display: flex;
        justify-content: space-between;
        padding: 20px;
        box-sizing: border-box;
        pointer-events: none;
        z-index: 1;

        button {
            pointer-events: all;
            border: none;
            border-radius: 999vw;
            background: var(--background);
            color: var(--text-color);
            width: calc(var(--font-size-lg) * 2);
            aspect-ratio: 1;
            padding: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
            opacity: 1;
            transition: opacity .2s ease, outline .2s ease;
            box-shadow: 0px 0px 5px var(--background);
            outline: 2px solid transparent;
            
            &.hidden {
                opacity: 0;
                pointer-events: none;
            }

            &.is_default_plan {
              outline: 2px solid rgb(219, 174, 0);
            }

            &::before {
                content: "";
                position: absolute;
                inset: 0;
                background: rgba(255, 255, 255, 0.1);
                pointer-events: none;
            }

            span {
                position: absolute;
                font-size: var(--font-size-lg);

                // Visually Centering Arrows
                &.left {
                    margin-left: -4px;
                }
                
                &.right {
                    margin-right: -4px;
                }
            }
        }
    }

    .plan-heading {
        font-size: var(--font-size-md);
        line-height: normal;
        font-weight: 700;
        margin-bottom: 15px;

        @media only screen and (min-width: 1501px) {
            font-size: var(--font-size-lg);
        }
    }

    .plus-btn {
        float: right;
        border: none;
        padding: 0px 10px;
        font-size: var(--font-size-base);
        height: clamp(calc(1.063rem + 15px), calc(4vw + 15px), calc(2.28rem + 15px));
        // aspect-ratio: 1;
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.08);
        color: var(--text-color);
        display: flex;
        justify-content: center;
        align-items: center;
        transition: background-color .2s ease;
        margin-left: 20px;

        &:hover, &:focus-visible {
            background-color: rgba(255, 255, 255, 0.05);
        }
    }

    .plan {
        & > div, & .lessons-wrapper {
            &:empty {
                outline-color: transparent !important;
            }
            position: relative;
            display: flex;
            flex-direction: column;
            gap: 10px;
            outline: solid 3px transparent;
            outline-offset: 5px;
            @media only screen and (max-width: 601px) {
                outline-width: 2px;
                outline-offset: 1px;
            }
        }
    }

    .extra-height {
        min-height: calc(100vh - 82px);

        @media only screen and (min-width: 1501px) {
            min-height: calc(100vh - 90px);
        }
    }

    .custom-badge {
      display: inline-flex;
      flex-direction: row;
      column-gap: .3em;
      align-items: center;

      background: rgba(255, 255, 255, 0.07);
      padding: 2px 7px;
      border-radius: 5px;
      white-space: nowrap;
      margin-bottom: .2em;
    }

    .no-linebreak {
        white-space: nowrap;
    }

    .lessons-wrapper {
        --bar-width: 10px;
        .lesson-time {
            position: relative;
            margin-left: -10px;
            background: rgba(255, 255, 255, 0.1);
            width: max-content;
            border-radius: 0px 8px 8px 0px;
        
            font-size: 1.3rem;

            padding: 1rem;
            line-height: 1;
            
            @media only screen and (max-width: 601px) {
                margin-left: 0px;
                border-radius: 5px;
        
                font-size: 0.875rem;
                padding: 5px;
                line-height: normal;
            }

            &.gap::before {
                content: "";
                position: absolute;
                top: calc(-1 * var(--bar-width));
                left: calc(-1 * var(--bar-width));

                width: var(--bar-width);
                aspect-ratio: 1;

                background: radial-gradient(circle at 50% -15% , transparent calc(.5 * var(--bar-width)), var(--background) calc(.5 * var(--bar-width) + .5px));
            }
            
            &.gap::after {
                content: "";
                position: absolute;
                top: 0px;
                left: calc(-1 * var(--bar-width));

                width: var(--bar-width);
                aspect-ratio: 1;

                background: radial-gradient(circle at 100% 100% , transparent var(--bar-width), var(--background) calc(var(--bar-width) + .5px));
            }
        }

        .deco-bar {
            position: absolute;
            top: 0;
            left: calc(-1 * var(--bar-width) - 10px);
    
            background: rgba(255, 255, 255, 0.1);
            height: 100%;
            width: var(--bar-width);
    
            border-radius: var(--bar-width) 0px var(--bar-width) var(--bar-width);
    
            @media only screen and (max-width: 601px) {
                display: none;
            }
        }
    }
</style>