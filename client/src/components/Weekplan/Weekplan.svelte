<script>
    import Lesson from './Lesson.svelte';
    import {onMount} from "svelte";
    import {arraysEqual, format_date, replace_page} from "../../utils.js";
    import {selected_favorite, title} from "../../stores.js";
    import {sameBlock} from "../../plan.js";
    import {getLabelOfPeriods} from "../../periods_utils.js";
    import Rooms from "../Rooms.svelte";

    export let api_base;
    export let school_num;
    export let date;
    export let plan_type;
    export let plan_value;
    export let meta;
    export let extra_height = true;
    export let week_letter = "";
    export let all_rooms;
    export let selected_revision;
    export let enabled_dates;
    export let free_days;
    export let available_plan_version;
    let used_rooms_hidden = true;

    onMount(() => {
        if(!school_num) {
            replace_page('school_manager');
        }
        title.set("Wochenplan");
    });

    // TODO: Remove
    let test_lesson = {
        "begin": "08:00",
        "class_number": "353",
        "current_class": "5Et12",
        "current_forms": [
            "5/1",
            "5/2"
        ],
        "current_forms_str": "5/1,2",
        "current_rooms": [
            "214"
        ],
        "current_teachers": [
            "CRL"
        ],
        "end": "09:30",
        "forms_changed": false,
        "info": [],
        "is_unplanned": false,
        "periods": [
            1,
            2
        ],
        "room_changed": false,
        "scheduled_class": "5Et12",
        "scheduled_forms": [
            "5/1",
            "5/2"
        ],
        "scheduled_forms_str": "5/1,2",
        "scheduled_rooms": [
            "214",
            "215"
        ],
        "scheduled_teachers": [
            "CRL"
        ],
        "subject_changed": false,
        "takes_place": true,
        "teacher_changed": false
    };

    let test_rooms_data = {
        "free_rooms_by_block": {
            "1": [
                "1"
            ]
        }
    };

    let full_teacher_name = "Crazy bro";

    const plan_type_map = {
        "forms": "Klasse",
        "rooms": "Raum",
        "teachers": "Lehrer"
    };

    // TODO: null setzen wenn nicht verfügbar
    let week_info = {
        start: new Date("2024-03-18"),
        type: "A"
    };

    // TODO: entfernen
    plan_type = "forms";
    plan_value = "5/1"

    // TODO: Logic
    let preferences_apply = true;

    const lesson_start = 1;
    const lesson_end = 10;
    const lesson_count = lesson_end - lesson_start + 1;

    const block_start = 1;
    const block_end = 5;
    const block_count = block_end - block_start + 1;
</script>

{#if plan_type !== "room_overview"}
    <!-- TODO: Vorhersage von einem Tag mit orangenem Rand anzeigen -->
    {#if week_info && plan_type && plan_value}
        {#if plan_type === "forms" && ($selected_favorite !== -1)}
            <button on:click={() => {preferences_apply = !preferences_apply}} class="plus-btn">{preferences_apply ? "Alle Stunden anzeigen" : "Nur ausgewählte anzeigen"}</button>
        {/if}
        <h1 class="plan-heading">
            Woche für {plan_type_map[plan_type]} <span class="custom-badge">{plan_value}{#if plan_type === "teachers"}{#if full_teacher_name !== null}{` (${full_teacher_name})`}{/if}{/if}</span> vom <span class="custom-badge">{format_date(week_info.start)}</span> <span class="no-linebreak">{#if week_info.type}({week_info.type}-Woche){/if}</span>
        </h1>
    {/if}

    <div class="week" style="">
        <div class="time-indicators">
            <div class="block-col">
                {#each {length: block_count} as _, i}
                    <span>{i + block_start}</span>
                {/each}
            </div>
            <div class="lesson-col">
                {#each {length: lesson_count} as _, i}
                    <span>{i + lesson_start}</span>
                {/each}
            </div>
        </div>
        {#each {length: 5} as _, i}
        <div class="day" class:last={i === 4}>
            <h2 class="day-heading">Mon. 11.3.</h2>
            {#if false} <!-- loading -->
                <span class="responsive-text">Lädt...</span>
            {:else if false} <!-- loading_failed -->
                <span class="responsive-text">Plan konnte nicht geladen werden.</span>
            {:else}
                {#if false} <!-- lessons.length === 0 -->
                    {#if plan_type}
                        <span class="responsive-text">Keine Stunden</span>
                    {:else}
                        <!-- <span class="responsive-text">Wähle eine Klasse, einen Lehrer, einen Raum oder die Raumübersicht aus, um {#if is_default_plan}eine Planvorhersage{:else}einen Plan{/if} zu sehen.</span>-->
                    {/if}
                {:else}
                    <!-- Day Content -->
                    {#each {length: block_count} as _, i}
                        <div class="block">
                            <div class="blocks-container">
                                <Lesson lesson={test_lesson} bind:plan_type bind:plan_value bind:date />
                            </div>
                            <div class="lessons-container">
                                <div class="lesson top">
                                </div>
                                <div class="lesson bottom">
                                </div>
                            </div>
                        </div>
                    {/each}
                {/if}
            {/if}
        </div>
        {/each}
    </div>
{:else}
    <button on:click={() => {used_rooms_hidden = !used_rooms_hidden}} class="plus-btn">{used_rooms_hidden ? "Besetzte Räume anzeigen" : "Nur freie Räume anzeigen"}</button>
    {#if week_info}
        <h1 class="plan-heading">Freie Räume in der Woche vom <span class="custom-badge">{format_date(week_info.start)}</span> <span class="no-linebreak"/>({week_info.type}-Woche)</h1>
    {/if}
    {#if false} <!-- loading -->
        <span class="responsive-text">Lädt...</span>
    {:else if false} <!-- loading_failed -->
        <span class="responsive-text">Plan{#if is_default_plan}vorhersage{/if} konnte nicht geladen werden</span>
    {:else}
        <div class="free_rooms_week">
            {#each {length: 5} as _, i}
                <div>
                    <h1 class="plan-heading" style="white-space: nowrap;">Mon. 11.03.</h1>
                    <Rooms rooms_data={test_rooms_data} bind:plan_type bind:plan_value bind:all_rooms bind:used_rooms_hidden />
                </div>
            {/each}
        </div>
    {/if}
{/if}
<!--
<div class="day-controls">
    <button tabindex="-1" on:click={() => {change_day(-1);}} class:hidden={!show_left_key}><span class="material-symbols-outlined left">arrow_back_ios_new</span></button>
    <button tabindex="-1" on:click={() => {change_day(1);}} class:hidden={!show_right_key}><span class="material-symbols-outlined right">arrow_forward_ios</span></button>
</div>
-->
<style lang="scss">
  $lesson_height: 4.7rem;

  .free_rooms_week {
    display: flex;
    flex-direction: row;
    gap: 1rem;
    overflow-x: auto;
    width: 100%;

    & > div {
      min-width: min(70vw, 25rem);
    }
  }

  .week {
    display: flex;
    flex-direction: row;

    width: 100%;
    overflow-x: auto;

    .time-indicators {
      display: flex;
      flex-direction: row;
      gap: 0.5rem;
      margin-right: 0.5rem;
      margin-top: calc(var(--font-size-lg) + .5rem);

      .block-col {
        display: flex;
        flex-direction: column;

        span {
          height: calc(2 * $lesson_height + .5rem);
          line-height: calc(2 * $lesson_height + .5rem);
          font-weight: bold;
          font-size: var(--font-size-lg);
          text-align: center;
        }
      }

      .lesson-col {
        display: flex;
        flex-direction: column;

        span {
          height: calc($lesson_height + .25rem);
          line-height: calc($lesson_height + .25rem);
          opacity: 0.5;
          text-align: center;
        }
      }
    }

    .day {
      display: flex;
      flex-direction: column;
      width: max-content;
      border-left: 1.5px solid rgba(255, 255, 255, 0.4);
      border-bottom: 1.5px solid rgba(255, 255, 255, 0.4);

      &.last {
        border-right: 1.5px solid rgba(255, 255, 255, 0.4);
      }

      padding: 0 .5rem;

      .day-heading {
        height: var(--font-size-lg);
        line-height: var(--font-size-lg);
        font-size: var(--font-size-lg);
        font-weight: bold;
        margin-bottom: 0.5rem;
        white-space: nowrap;
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

        height: calc(2 * $lesson_height);
        display: flex;
        flex-direction: row;

        .blocks-container {
          height: calc(2 * $lesson_height);
          display: flex;
          flex-direction: row;
          gap: .2rem;
          padding: .2rem;
          box-sizing: border-box;
        }

        .lessons-container {
          height: calc(2 * $lesson_height);
          display: flex;
          flex-direction: column;

          .lesson {
            height: $lesson_height;
            gap: .2rem;
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
</style>