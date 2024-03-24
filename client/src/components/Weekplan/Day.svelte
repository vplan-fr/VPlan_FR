<script>
    import Lesson from "./Lesson.svelte";
    import {
        indexed_db,
        settings,
        selected_favorite,
        favorites,
        api_base,
        active_modal,
        inspecting_day
    } from "../../stores.js";
    import {
        load_plan,
        load_lessons,
        apply_preferences,
        get_teacher_data,
        get_plan_version,
        gen_revision_arr,
        getDateDisabled
    } from "../../plan.js";
    import Select from "../../base_components/Select.svelte";
    import Rooms from "../Rooms.svelte";
    import {format_date} from "../../utils.js";

    export let school_num;
    export let first;
    export let last;
    export let plan_type;
    export let plan_value;
    export let date;
    export let block_count;
    export let meta;
    export let enabled_dates;
    export let free_days;
    export let week_letter;
    export let all_rooms;
    export let used_rooms_hidden;
    export let preferences_apply;
    export let full_teacher_name;
    export let teacher_contact_link = null;
    export let teacher_image_path = null;

    let revision_arr;
    $: revision_arr = gen_revision_arr([".newest"].concat((meta?.dates || {})[date] || []));
    let selected_revision = ".newest";
    let info;
    let plan_data = [];
    let all_lessons = [];
    let rooms_data = {};
    let last_fetch;
    let is_default_plan = false;
    let loading = false;
    let loading_failed = false;
    let cache_loading_failed = false;
    let network_loading_failed = false;
    let data_from_cache = false;
    let caching_successful = false;
    let last_updated = {};
    let exams;
    let sorted_lessons;
    const plan_type_map = {
        "forms": "Klasse",
        "rooms": "Raum",
        "teachers": "Lehrer"
    };
    let controller = new AbortController();

    function format_date_heading(date) {
        date = new Date(date);
        const days = [
            "So",
            "Mo",
            "Di",
            "Mi",
            "Do",
            "Fr",
            "Sa"
        ];

        const weekday = days[date.getDay()];

        return `${weekday} ${date.getDate()}.`
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

    function handle_last_updated(given_date, renew) {
        if(!renew) {
            return last_updated[given_date] || new Date(1970, 1, 1);
        }

        last_updated[given_date] = new Date();
    }

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
    $: meta && load_lessons(plan_data, school_num, plan_type, plan_value, $settings.use_grouped_form_plans, meta, reset_plan_vars, update_lessons);
    // Apply Preferences to lessons
    $: lessons = sort_lessons(apply_preferences(plan_type, preferences_apply, $selected_favorite, $favorites, all_lessons));

    // === Load Extra Teacher Data ===
    // Get teacher data (Name, Contact and Image Link)
    $: if(plan_type === "teachers") {
        [full_teacher_name, teacher_contact_link, teacher_image_path] = get_teacher_data(meta.teachers, plan_value, school_num);
    }

    // === UI + Navigation ===
    // Get if loading failed
    $: loading_failed = (cache_loading_failed && network_loading_failed && !loading);

    // Get plan version string
    $: available_plan_version = get_plan_version(is_default_plan, data_from_cache, network_loading_failed, caching_successful);

    function sort_lessons(lessons) {
        // TODO: after block refactor
        let tmp_out = Array.from({length: block_count}, (v, i) => [[], [], []]); // [[blocks], [top halfs], [bottom halfs]]
        for(const lesson of lessons) {
            tmp_out[
                Math.floor((lesson.periods[0] + 1) / 2)-1
                ][
                    lesson.periods.length > 1 ? 0 : (lesson.periods[0] % 2 == 0 ? 2 : 1)
                ].push(lesson);
        }
        return tmp_out;
    }
</script>
<div class="day"
     class:first
     class:last
     class:cached={available_plan_version === "cached"}
     class:network_cached={available_plan_version === "network_cached"}
     class:network_uncached={available_plan_version === "network_uncached"}
     class:is_default_plan={available_plan_version === "default_plan"}
     class:room_overview={plan_type === "room_overview"}
     class:invalid_date={loading_failed || getDateDisabled(enabled_dates, free_days, date)}
>
    <h2 class="day-heading">
        {date ? format_date_heading(date) : "..."}
        {#if (exams && Object.keys(exams).length !== 0) || info}
            <button class="info-btn" class:infos-available={info && info.additional_info.length > 0} class:exams-available={exams && Object.keys(exams).length !== 0} on:click={() => {
                $active_modal = "day-inspect";
                $inspecting_day = {
                    info: info,
                    exams: exams,
                    is_default_plan: is_default_plan,
                    last_fetch: last_fetch,
                    date: date ? format_date(date) : "..."
                };
            }}>
                <span class="material-symbols-outlined">info</span>
            </button>
        {/if}
    </h2>
    {#if loading}
        <span class="responsive-text" style="white-space: nowrap; padding: 1rem 2rem;">Tag Lädt...</span>
    {:else if getDateDisabled(enabled_dates, free_days, date)}
        <span class="responsive-text" style="min-width: 8rem;">Kein Plan verfügbar.</span>
    {:else if loading_failed}
        <span class="responsive-text" style="min-width: 8rem;">Plan konnte nicht geladen werden.</span>
    {:else}
        {#if lessons.length === 0}
            {#if plan_type}
                <span class="responsive-text">Keine Stunden</span>
            {:else}
                <span class="responsive-text">Wähle eine Klasse, einen Lehrer, einen Raum oder die Raumübersicht aus, um {#if is_default_plan}eine Planvorhersage{:else}einen Plan{/if} zu sehen.</span>
            {/if}
        {:else}
            {#if plan_type !== "room_overview"}
                <!-- Day Content -->
                {#each {length: block_count} as _, i}
                    <div class="block">
                        {#if lessons[i][0].length > 0}
                            <div class="blocks-container" class:filled_in_weekplan={$settings.filled_in_weekplan}>
                                {#each lessons[i][0] as lesson}
                                    <Lesson lesson={lesson} bind:plan_type bind:plan_value />
                                {/each}
                            </div>
                        {/if}
                        {#if lessons[i][1].length > 0 || lessons[i][2].length > 0}
                            <div class="lessons-container" class:filled_in_weekplan={$settings.filled_in_weekplan}>
                                <div class="lesson top">
                                    {#each lessons[i][1] as lesson}
                                        <Lesson lesson={lesson} bind:plan_type bind:plan_value />
                                    {/each}
                                </div>
                                <div class="lesson bottom">
                                    {#each lessons[i][2] as lesson}
                                        <Lesson lesson={lesson} bind:plan_type bind:plan_value />
                                    {/each}
                                </div>
                            </div>
                        {/if}
                    </div>
                {/each}
            {:else}
                <Rooms bind:rooms_data bind:plan_type bind:plan_value bind:all_rooms bind:used_rooms_hidden />
            {/if}
        {/if}
    {/if}
</div>

<style lang="scss">
  .invalid_date > h2 > .info-btn {
    display: none;
  }

  .info-btn {
    --padding: .2rem;
    z-index: 1;
    padding: var(--padding);
    background: rgba(255, 255, 255, 0.1);
    border: none;
    height: calc(var(--font-size-base) + var(--padding) * 2);
    width: calc(var(--font-size-base) + var(--padding) * 2);
    line-height: var(--font-size-base);
    @media only screen and (max-width: 900px) {
      height: calc(var(--font-size-sm) + var(--padding) * 2);
      width: calc(var(--font-size-sm) + var(--padding) * 2);
      line-height: var(--font-size-sm);
    }
    border-radius: 9vw;

    &.infos-available {
      background: rgba(255, 255, 255, 0.2);

      .material-symbols-outlined {
        color: var(--text-color);
      }
    }

    &.exams-available {
      background: var(--accent-color);

      .material-symbols-outlined {
        color: var(--text-color);
      }
    }

    .material-symbols-outlined {
      font-size: var(--font-size-base);
      @media only screen and (max-width: 900px) {
        font-size: var(--font-size-sm);
      }
      padding: 0;
      color: rgba(255, 255, 255, 0.2);
    }
  }

  .day {
    display: flex;
    flex: 1;
    flex-direction: column;
    width: max-content;
    border-left: 1.5px solid rgba(255, 255, 255, 0.4);
    border-bottom: 1.5px solid rgba(255, 255, 255, 0.4);

    &.room_overview {
      min-width: 20rem;
    }

    box-shadow: 0 1.5px 0 rgba(255, 255, 255, 0.6) inset;

    &.cached {
      box-shadow: 0 1.5px 0 rgba(255, 255, 255, 0.6) inset;
    }

    &.network_cached {
      box-shadow: 0 1.5px 0 rgba(0, 219, 0, 0.6) inset;
    }

    &.network_uncached {
      box-shadow: 0 1.5px 0 rgba(219, 174, 0, 0.6) inset;
    }

    &.is_default_plan {
      box-shadow: 0 1.5px 0 rgba(219, 174, 0, 0.6) inset;
    }

    &.invalid_date {
      box-shadow: 0 1.5px 0 var(--cancelled-color) inset;
    }

    &.first {
      border-right: 1.5px solid rgba(255, 255, 255, 0.4);
      border-radius: 1rem 0 0 0;
      @media only screen and (max-width: 900px) {
        border-radius: .5rem 0 0 0;
      }
    }

    &.last {
      border-right: 1.5px solid rgba(255, 255, 255, 0.4);
      border-radius: 0 1rem 0 0;
      @media only screen and (max-width: 900px) {
        border-radius: 0 .5rem 0 0;
      }
    }

    padding: 0 .5rem;
    @media only screen and (max-width: 900px) {
      padding: 0 .3rem;
    }

    .day-heading {
      height: var(--font-size-lg);
      line-height: var(--font-size-lg);
      font-size: var(--font-size-lg);
      @media only screen and (max-width: 900px) {
        font-size: var(--font-size-base);
        height: var(--font-size-base);
        line-height: var(--font-size-base);
      }
      font-weight: bold;
      margin-bottom: 0.5rem;
      margin-top: 0.3rem;
      white-space: nowrap;
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      align-items: center;
      gap: 0.5rem;
      @media only screen and (max-width: 900px) {
        gap: 0.3rem;
      }
    }

    .block {
      position: relative;
      padding: .25rem 0;

      &::before {
        content: "";
        position: absolute;
        z-index: -1;
        width: calc(100% + 1rem);
        border-top: 1px solid rgba(255, 255, 255, 0.2);
        top: 50%;
        left: 50%;
        transform: translateY(-50%) translateX(-50%);
      }

      &::after {
        content: "";
        position: absolute;
        z-index: -1;
        width: calc(100% + 1rem);
        border-top: 1px solid rgba(255, 255, 255, 0.2);
        top: 0;
        left: 50%;
        transform: translateX(-50%);
      }

      height: calc(2 * var(--lesson-height));
      display: flex;
      flex-direction: row;

      .blocks-container {
        height: calc(2 * var(--lesson-height));
        display: flex;
        flex-direction: row;
        gap: .4rem;
        padding: .2rem;
        box-sizing: border-box;

        &.filled_in_weekplan {
            flex: 1
        }
      }

      .lessons-container {
        height: calc(2 * var(--lesson-height));
        display: flex;
        flex-direction: column;

        &.filled_in_weekplan {
          flex: 1
        }

        .lesson {
          height: var(--lesson-height);
          gap: .4rem;
          padding: .2rem;
          box-sizing: border-box;
          display: flex;
          flex-direction: row;

          &.top {
            padding-bottom: .3rem;
          }
          &.bottom {
            padding-top: .3rem;
          }
        }
      }
    }
  }
</style>