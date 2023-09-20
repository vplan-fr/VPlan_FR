<script>
    import {onMount} from 'svelte';
    import Lesson from './Lesson.svelte';
    import Rooms from "./Rooms.svelte";
    import {notifications} from './notifications.js';
    import { swipe } from 'svelte-gestures';
    import {preferences, settings, title} from './stores.js';
    import {arraysEqual, customFetch, format_date, navigate_page, should_date_be_cached} from "./utils.js";

    export let api_base;
    export let school_num;
    export let date;
    export let plan_type;
    export let plan_value;
    export let all_meta;
    export let show_title = true;
    export let extra_height = true;
    export let week_letter = "";
    export let external_times = true;
    export let all_rooms;
    export let selected_revision;
    export let enabled_dates;
    let used_rooms_hidden = true;

    let all_lessons = [];
    let rooms_data = {};
    let info;
    let loading = false;
    let loading_failed = false;
    let data_from_cache = false;
    let plan_type_map = {
        "forms": "Klasse",
        "rooms": "Raum",
        "teachers": "Lehrer"
    };
    let controller = new AbortController();

    function reset_plan_vars() {
        info = null;
        all_lessons = [];
        rooms_data = null;
        plan_type = null;
        plan_value = null;
    }

    export function load_lessons(date, c_plan_type, entity, use_grouped_form_plans, revision=".newest") {
        let plan_key = use_grouped_form_plans ? "grouped_form_plans": "plans";
        controller.abort();
        // Check the presence of necessary variables
        if (date === null || date === undefined || !c_plan_type || ((c_plan_type !== "room_overview") && !entity)) {
            reset_plan_vars();
            return;
        }
        // Check the validity of the plan type
        if(!enabled_dates.includes(date) || !["forms", "rooms", "teachers", "room_overview"].includes(c_plan_type)) {
            reset_plan_vars();
            return;
        }
        // Check the validity of the plan value
        if((plan_type === "rooms" || plan_type === "teachers") && (!Object.keys(all_meta[plan_type]).includes(entity))) {
            reset_plan_vars();
            return;
        } else if((plan_type === "forms") && !Object.keys(all_meta["forms"]["forms"]).includes(entity)) {
            reset_plan_vars();
            return;
        }

        console.log("Loading lessons...", date, c_plan_type, entity);

        loading = true;
        data_from_cache = false;
        loading_failed = false;
        controller = new AbortController();
        //console.log("getting lesson plan", school_num, date);
        if (should_date_be_cached(date) && revision === ".newest") {
            let data = localStorage.getItem(`${school_num}_${date}`);
            if (data !== "undefined" && data) {
                data = JSON.parse(data);
                rooms_data = data["rooms"];
                if (c_plan_type !== "room_overview") {
                    all_lessons = data[plan_key][c_plan_type] ? data[plan_key][c_plan_type][entity] || [] : [];
                }
                info = data["info"];
                week_letter = info["week"];

                data_from_cache = true;
                loading = false;
            }
        }
        let params = new URLSearchParams();
        params.append("date", date);
        params.append("revision", revision);
        customFetch(`${api_base}/plan?${params.toString()}`, {signal: controller.signal})
            .then(data => {
                if (Object.keys(data).length !== 0 && should_date_be_cached(date) && revision === ".newest") {
                    try {
                        localStorage.setItem(`${school_num}_${date}`, JSON.stringify(data));
                    } catch (error) {
                        if (error.name === 'QuotaExceededError' ) {
                            notifications.danger("Der aktuelle Plan konnte nicht gecached werden.")
                        } else {
                            throw error;
                        }
                    }
                }
                rooms_data = data["rooms"]
                if (c_plan_type !== "room_overview") {
                    all_lessons = data[plan_key][c_plan_type][entity] || [];
                }
                info = data["info"];
                week_letter = info["week"];
                //console.log(lessons);
                
                loading = false;
            })
            .catch(error => {
                if (error.name === "AbortError") {
                } else if (data_from_cache) {
                    loading_failed = false;
                    loading = false;
                    notifications.info("Plan aus Cache geladen", 2000);
                } else {
                    loading_failed = true;
                    loading = false;
                    notifications.danger("Plan konnte nicht geladen werden.");
                }
        });
        location.hash = gen_location_hash();
    }

    function periods_to_block_label(periods) {
        periods.sort(function (a, b) {  return a - b;  });

        const rests = {
            0: "/Ⅱ",
            1: "/Ⅰ",
        };

        if (periods.length === 1) {
            return `${Math.floor((periods[0] - 1) / 2) + 1}${rests[periods[0] % 2]}`;
        } else if (periods.length === 2 && periods[0] % 2 === 1) {
            return `${Math.floor(periods[periods.length - 1] / 2)}`;
        } else {
            return periods.map(p => periods_to_block_label([p])).join(", ");
        }
    }

    function sameBlock(a, b) {
        return a.includes(b[0]) || a.includes(b[1])
    }

    function format_timestamp(timestamp) {
        const date = new Date(timestamp);

        const targetTimezone = 'Europe/Berlin';
        const options = {
            timeZone: targetTimezone,
            weekday: 'long',
            month: 'long',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        };
        const formatter = new Intl.DateTimeFormat('de-DE', options);
        const formattedDate = formatter.format(date).replace("um", "-") + " Uhr";

        return `${formattedDate}`;
    }

    $: load_lessons(date, plan_type, plan_value, $settings.use_grouped_form_plans, selected_revision);

    function gen_location_hash() {
        if(school_num && date && plan_type) {
            return `#plan|${school_num}|${date}|${plan_type}|${plan_value}`;
        } else {
            return "#plan";
        }
    }

    function refresh_plan_vars() {
        let tmp_variables = location.hash.split("|");
        if (tmp_variables.length === 5) {
            school_num = decodeURI(tmp_variables[1]);
            date = decodeURI(tmp_variables[2]);
            plan_type = decodeURI(tmp_variables[3]);
            plan_value = decodeURI(tmp_variables[4]);
        }
    }
    refresh_plan_vars();

    if(!school_num) {
        navigate_page('school_manager');
    }

    onMount(() => {
        location.hash = gen_location_hash();
        title.set("Plan");
        // console.log("Mounted Plan.svelte");
    });

    window.addEventListener('popstate', (e) => {
        refresh_plan_vars();
    });

    let full_teacher_name = null;
    let teacher_contact_link = null;
    $: if (plan_type === "teachers") {
        full_teacher_name = all_meta["teachers"][plan_value]?.surname || null;
        teacher_contact_link = all_meta["teachers"][plan_value]?.contact_link || null;
    }

    let preferences_apply = true;
    let lessons = all_lessons;
    function render_lessons(lessons) {
        if (plan_type !== "forms") {
            return lessons
        }
        if (!preferences_apply) {
            return lessons
        }
        if (!(plan_value in $preferences)) {
            return lessons
        }
        let cur_preferences = $preferences[plan_value] || [];
        let new_lessons = [];
        for (const lesson of lessons) {
            if (!(cur_preferences.includes(lesson["class_number"]))) {
                new_lessons.push(lesson);
            }
        }
        return new_lessons;
    }

    function change_day(day_amount) {
        let tmp_date;
        tmp_date = enabled_dates[(enabled_dates.indexOf(date)+day_amount)];
        if (typeof tmp_date === 'undefined') {
            notifications.danger("Für dieses Datum existiert kein Vertretungsplan!");
            return;
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

    let show_left_key = true;
    let show_right_key = true;
    function update_date_btns() {
        show_left_key = enabled_dates.indexOf(date) > 0;
        show_right_key = enabled_dates.indexOf(date) < (enabled_dates.length - 1);
    }
    
    $: date && enabled_dates && update_date_btns();
    $: preferences_apply, lessons = render_lessons(all_lessons);
</script>

<svelte:window on:keydown={keydown_handler}/>
<svelte:body use:swipe={{ timeframe: 300, minSwipeDistance: 60, touchAction: 'pan-y' }} on:swipe={swipe_handler} />

{#if plan_type !== "room_overview"}
<div class="plan" class:extra-height={extra_height}>
    {#if show_title && info}
        {#if plan_type === "forms" && (plan_value in $preferences)}
            <button on:click={() => {preferences_apply = !preferences_apply}} class="plus-btn">{preferences_apply ? "+" : "-"}</button>
        {/if}
            <h1 class="plan-heading">
                Plan für {plan_type_map[plan_type]} <span class="custom-badge">{plan_value}{#if plan_type === "teachers"}{#if full_teacher_name !== null}{` (${full_teacher_name})`}{/if}{/if}</span> <span>am</span> <span class="custom-badge">{format_date(date)}</span> <span class="no-linebreak">({info.week}-Woche)</span>
            </h1>
        {/if}
    {#if loading}
        <span class="responsive-text">Lädt...</span>
    {:else if loading_failed}
        <span class="responsive-text">Plan konnte nicht geladen werden</span>
    {:else}
        {#if lessons.length === 0}
        {#if plan_type}    
            <span class="responsive-text">Keine Stunden</span>
        {:else}
        <span class="responsive-text">Wähle eine Klasse, einen Lehrer, einen Raum oder die Raumübersicht aus um einen Plan zu sehen.</span>
        {/if}
        {:else}
        <div class="lessons-wrapper">
            {#if external_times}
                <div class="deco-bar"></div>
            {/if}
            {#each lessons as lesson, i}
                {#if external_times}    
                    {#if !all_lessons[i-1] || (!arraysEqual(lesson.periods, lessons[i-1].periods))}
                        <span class="lesson-time" class:gap={lessons[i-1] && !sameBlock(lesson.periods, lessons[i-1].periods)}>{periods_to_block_label(lesson.periods)}: {lesson.begin} - {lesson.end}</span>
                    {/if}
                {/if}
                <Lesson lesson={lesson} bind:plan_type bind:plan_value bind:date display_time={!external_times} />
            {/each}
        </div>
        {/if}
        {#if info}
            {#if info.additional_info.length > 0}
                <div class="additional-info">
                    {#each info.additional_info as cur_info}
                        {#if cur_info !== null}
                            {cur_info}
                        {/if}
                        <br>
                    {/each}
                </div>
            {/if}
            <div class="last-updated">Stand der Daten: <span class="custom-badge">{format_timestamp(info.timestamp)}</span></div>
        {/if}
    {/if}
</div>
{:else}
<div class:extra-height={extra_height}>
    <button on:click={() => {used_rooms_hidden = !used_rooms_hidden}} class="plus-btn">{used_rooms_hidden ? "+" : "-"}</button>
    {#if info}
        <h1 class="plan-heading">Raumübersicht am <span class="custom-badge">{format_date(date)}</span> <span class="no-linebreak"/>({info.week}-Woche)</h1>
    {/if}
    {#if loading}
        <span class="responsive-text">Lädt...</span>
    {:else if loading_failed}
        <span class="responsive-text">Plan konnte nicht geladen werden</span>
    {:else}
        <Rooms rooms_data={rooms_data} bind:plan_type bind:plan_value bind:all_rooms bind:used_rooms_hidden />
        {#if info}
            <div class="last-updated">Stand der Daten: <span class="custom-badge">{format_timestamp(info.timestamp)}</span></div>
        {/if}
    {/if}
</div>
{/if}
<div class="day-controls">
    <button tabindex="-1" on:click={() => {change_day(-1);}} class:hidden={!show_left_key}><span class="material-symbols-outlined left">arrow_back_ios_new</span></button>
    <button tabindex="-1" on:click={() => {change_day(1);}} class:hidden={!show_right_key}><span class="material-symbols-outlined right">arrow_forward_ios</span></button>
</div>

<style lang="scss">
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
        line-height: 1.6;
        font-weight: 700;
        margin-bottom: 15px;

        @media only screen and (min-width: 1501px) {
            font-size: var(--font-size-xl);
        }
    }

    .plus-btn {
        float: right;
        border: none;
        font-size: var(--font-size-xl);
        height: clamp(calc(1.063rem + 15px), calc(4vw + 15px), calc(2.28rem + 15px));
        aspect-ratio: 1;
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
        min-height: calc(100vh - 66px);

        @media only screen and (min-width: 1501px) {
            min-height: calc(100vh - 74px);
        }
    }

    .custom-badge {
        background: rgba(255, 255, 255, 0.07);
        padding: 2px 7px;
        border-radius: 5px;
        white-space: nowrap;
    }

    .last-updated {
        font-size: clamp(0.875rem, 2.8vmin, 1.75rem);
        line-height: 1.5;
        margin-top: 20px;
        display: block !important;
    }

    .additional-info {
        position: relative;
        font-size: clamp(0.938rem, 3vmin, 1.875rem);
        line-height: 1.5;
        border: clamp(1px, .3vmax, 3px) solid rgba(255, 255, 255, 0.2);
        padding: 10px;
        padding-top: calc(1vmax + .5rem);
        margin-top: 30px;
        border-radius: 5px;

        &::before {
            content: "Informationen";
            color: rgba(255, 255, 255, 0.2);
            background: var(--background);
            padding: 0px 5px;
            position: absolute;
            top: 0;
            left: 20px;
            transform: translateY(-50%);
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
        
            font-size: 2rem;
            @media only screen and (max-width: 1500px) {
                font-size: 1.3rem;
            }

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