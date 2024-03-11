<script>
    import {onMount} from 'svelte';
    import Lesson from './Lesson.svelte';
    import Rooms from "./Rooms.svelte";
    import {notifications} from '../notifications.js';
    import { swipe } from 'svelte-gestures';
    import {indexed_db, settings, title, selected_favorite, favorites} from '../stores.js';
    import {arraysEqual, format_date, navigate_page, format_timestamp} from "../utils.js";
    import {sameBlock, get_plan_version, get_teacher_data, load_plan, gen_location_hash, load_lessons, apply_preferences} from "../plan.js";
    import {getLabelOfPeriods} from "../periods_utils.js";
    import Dropdown from '../base_components/Dropdown.svelte';

    export let api_base;
    export let school_num;
    export let date;
    export let plan_type;
    export let plan_value;
    export let meta;
    export let show_title = true;
    export let extra_height = true;
    export let week_letter = "";
    export let external_times = true;
    export let all_rooms;
    export let selected_revision;
    export let enabled_dates;
    export let free_days;
    export let available_plan_version;
    let used_rooms_hidden = true;

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
    let plan_type_map = {
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
    let show_right_key = true;
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
        last_fetch = data.last_fetch;
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

    function change_day(day_amount) {
        let tmp_date;
        tmp_date = enabled_dates[(enabled_dates.indexOf(date)+day_amount)];
        if (typeof tmp_date === 'undefined') {
            // Removed due to being more annoying than it bringing value to the UX
            // notifications.danger("Für dieses Datum existiert kein Vertretungsplan!");
            //return;
        }
        date = tmp_date;
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
        show_left_key = enabled_dates.indexOf(date) > 0;
        show_right_key = enabled_dates.indexOf(date) < (enabled_dates.length - 1);
    }

    function handle_last_updated(given_date, renew) {
        if(!renew) {
            return last_updated[given_date] || new Date(1970, 1, 1);
        }

        last_updated[given_date] = new Date();
    }

    if(!school_num) {
        navigate_page('school_manager');
    }

    onMount(() => {
        title.set("Plan");
    });

    // === Load Plan + Lessons ===
    // Check if new plan has to be loaded and load it
    $: $indexed_db, load_plan(
        api_base, 
        school_num, 
        date, 
        selected_revision, 
        enabled_dates,
        free_days,
        handle_last_updated, handle_loading_state, handle_plan_data, renew_abort_controller
    );
    // Load the new lessons on change to selected plan
    $: meta && load_lessons(plan_data, school_num, plan_type, plan_value, $settings.use_grouped_form_plans, meta, reset_plan_vars, update_lessons);
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
    $: available_plan_version = get_plan_version(data_from_cache, network_loading_failed, caching_successful);
    
    // Update location hash
    $: location.hash = gen_location_hash("plan", school_num, date, plan_type, plan_value);
</script>

<svelte:window on:keydown={keydown_handler}/>
<svelte:body use:swipe={{ timeframe: 300, minSwipeDistance: 60, touchAction: 'pan-y' }} on:swipe={swipe_handler} />

<div class:plan={plan_type !== "room_overview"} class:extra-height={extra_height}>
    {#if plan_type !== "room_overview"}
        {#if show_title && info && plan_type && plan_value}
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
            <span class="responsive-text">Plan konnte nicht geladen werden.</span>
        {:else}
            {#if lessons.length === 0}
            {#if plan_type}    
                <span class="responsive-text">Keine Stunden</span>
            {:else}
                <span class="responsive-text">Wähle eine Klasse, einen Lehrer, einen Raum oder die Raumübersicht aus, um einen Plan zu sehen.</span>
            {/if}
            {:else}
            <div class="lessons-wrapper">
                {#if external_times}
                    <div class="deco-bar"></div>
                {/if}
                {#each lessons as lesson, i}
                    {#if external_times}    
                        {#if !all_lessons[i-1] || (!arraysEqual(lesson.periods, lessons[i-1].periods))}
                            <span class="lesson-time" class:gap={lessons[i-1] && !sameBlock(lesson.periods, lessons[i-1].periods)}>{getLabelOfPeriods(lesson.periods)}{lesson.begin != null && lesson.end != null ? ": " + lesson.begin + " - " + lesson.end : ""}</span>
                        {/if}
                    {/if}
                    <Lesson lesson={lesson} bind:plan_type bind:plan_value bind:date display_time={!external_times} />
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
            <span class="responsive-text">Plan konnte nicht geladen werden</span>
        {:else}
            <Rooms rooms_data={rooms_data} bind:plan_type bind:plan_value bind:all_rooms bind:used_rooms_hidden />
        {/if}
    {/if}
    {#if exams && Object.keys(exams).length !== 0}
        <div class="additional-info exams">
            {#each Object.entries(exams) as [form, exam_list]}
                {#if exam_list.length > 0}
                    <div class="inline-wrapper">
                        Klausuren für <button on:click={() => {
                            plan_type = "forms";
                            plan_value = form;
                            selected_favorite.set(-1);
                        }} class="no-btn-visuals clickable">{form}</button>:
                        <ul>
                            {#each exam_list as exam}
                                <li>{exam.course} bei <button on:click={() => {
                                        plan_type = "teachers";
                                        plan_value = exam.course_teacher;
                                        selected_favorite.set(-1);
                                    }} class="no-btn-visuals clickable" style="color: var(--text-color); font-size: inherit; margin-top: 0.3em;">{exam.course_teacher}</button>: {exam.begin} Uhr ({exam.duration}min)</li>
                            {/each}
                        </ul>
                    </div>
                {:else}
                    <div class="info-spacer"></div>
                {/if}
            {/each}
        </div>
    {/if}
    {#if info}
        {#if info.additional_info.length > 0}
            <div class="additional-info">
                {#each info.processed_additional_info as info_paragraph}
                    {#if info_paragraph.length > 0}
                        <div class="inline-wrapper">
                            {#each info_paragraph as text_segment}
                                {#if text_segment.link?.value.length === 1}
                                    <button class="no-btn-visuals" on:click={() => {
                                        date = text_segment.link.date;
                                        plan_type = text_segment.link.type;
                                        plan_value = text_segment.link.value[0];
                                        selected_favorite.set(-1);
                                    }}>
                                        <div class="clickable">{text_segment.text}</div>
                                    </button>
                                {:else if text_segment.link?.value.length >= 2}
                                    <div class="fit-content-width">
                                        <Dropdown let:toggle small={true} transform_origin_x="50%">
                                            <button slot="toggle_button" on:click={toggle} class="toggle-button">
                                                <span class="grow">{text_segment.text}</span>
                                                <span class="material-symbols-outlined dropdown-arrow">arrow_drop_down</span>
                                            </button>

                                            {#each text_segment.link.value as item}
                                                <button on:click={() => {
                                                    date=text_segment.link.date;
                                                    plan_type = text_segment.link.type;
                                                    plan_value = item;
                                                    selected_favorite.set(-1);
                                                }}>{item}</button>
                                            {/each}
                                        </Dropdown>
                                    </div>
                                {:else}
                                    {text_segment.text}
                                {/if}
                            {/each}
                        </div>
                    {:else}
                        <div class="info-spacer"></div>
                    {/if}
                {/each}
            </div>
        {/if}
        <div class="last-updated">
            Plan zuletzt aktualisiert: <span class="custom-badge">{format_timestamp(info.timestamp)}</span><br>
            Zuletzt auf neue Pläne überprüft: <span class="custom-badge">{format_timestamp(last_fetch)}</span></div>
    {/if}
</div>
<div class="day-controls">
    <button tabindex="-1" on:click={() => {change_day(-1);}} class:hidden={!show_left_key}><span class="material-symbols-outlined left">arrow_back_ios_new</span></button>
    <button tabindex="-1" on:click={() => {change_day(1);}} class:hidden={!show_right_key}><span class="material-symbols-outlined right">arrow_forward_ios</span></button>
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

    .inline-wrapper > * {
        font-size: inherit;
        color: var(--text-color);
        white-space: pre-wrap;
        word-break: break-word;
    }

    .info-spacer {
        height: 5px;
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

    .fit-content-width {
        width: fit-content;
    }

    .fit-content-width .dropdown-wrapper button, .max-width .dropdown-wrapper button {
        border: none;
        background: transparent;
        color: var(--text-color);
        transition: background-color .2s ease;
        width: 100%;
        padding: 2px 0px 2px 5px;
        font-size: inherit;

        &:hover, &:focus-visible {
            background-color: rgba(0, 0, 0, 0.5);
        }

        &.toggle-button {
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 5px;
            overflow: hidden;
            text-align: left;
            font-size: inherit;
            font-weight: inherit;
            color: var(--text-color);

            span.grow {
                flex: 1;
                white-space: nowrap;
            }
            
            &.center-align {
                text-align: center;
            }

            &:hover, &:focus-visible {
                background-color: rgba(255, 255, 255, 0.15);
            }
        }
    }

    .no-btn-visuals {
        border: 0;
        background: none;
        padding: 0;
        margin: 0;
        text-align: start;
    }

    .clickable {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 5px;
        padding: 2px 5px;
        transition: background-color 0.2s ease;

        &:hover, &:focus-visible {
            background-color: rgba(255, 255, 255, 0.2);
        }
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
            transition: opacity .2s ease;
            box-shadow: 0px 0px 5px var(--background);
            
            &.hidden {
                opacity: 0;
                pointer-events: none;
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

    .last-updated {
        font-size: var(--font-size-base);
        line-height: 1.5;
        margin-top: 20px;
        display: block !important;
    }

    .additional-info {
        position: relative;
        font-size: var(--font-size-base);
        line-height: 1.5;
        border: clamp(1px, .3vmax, 3px) solid rgba(255, 255, 255, 0.2);
        padding: 10px;
        padding-top: calc(10px + var(--font-size-md) / 2);
        margin-top: 30px;
        border-radius: 5px;

        &::before {
            content: "Informationen";
            font-size: var(--font-size-md);
            color: rgba(255, 255, 255, 0.2);
            background: var(--background);
            padding: 0px 5px;
            position: absolute;
            top: 0;
            left: 20px;
            transform: translateY(-50%);
        }

        &.exams::before {
            content: "Klausuren";
        }
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