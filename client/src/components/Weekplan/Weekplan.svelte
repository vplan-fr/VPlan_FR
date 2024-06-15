<script>
    import {onMount} from "svelte";
    import {format_date, replace_page, replace_hash, update_hash} from "../../utils.js";
    import {gen_location_hash, getDateDisabled} from "../../plan.js";
    import {selected_favorite, settings, title} from "../../stores.js";
    import Day from "./Day.svelte";
    import {BlockConfiguration} from "../../periods_utils.js";

    // Force date to be monday
    $: date, (() => {
        let tmp_date = firstDayOfWeek(new Date(date), 1);
        date = `${tmp_date.getFullYear()}-${pad(tmp_date.getMonth()+1)}-${pad(tmp_date.getDate())}`;
    })();

    export let school_num;
    export let date;
    export let plan_type;
    export let plan_value;
    export let meta;
    export let all_rooms;
    export let enabled_dates;
    export let free_days;
    export let block_config;
    const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s);
    let used_rooms_hidden = true;
    let show_left_key = true;
    let left_key_default_plan = false;
    let show_right_key = true;
    let right_key_default_plan = false;
    let week_type;
    let week_dates = [];
    let full_teacher_name;
    let teacher_contact_link;
    let teacher_image_path;

    function change_day(direction) {
        let tmp_date = new Date(date);
        tmp_date.setDate(tmp_date.getDate() + direction);
        date = `${tmp_date.getFullYear()}-${pad(tmp_date.getMonth()+1)}-${pad(tmp_date.getDate())}`;
    }

    function firstDayOfWeek(dateObject, firstDayOfWeekIndex) {
        const dayOfWeek = dateObject.getDay(),
            firstDayOfWeek = new Date(dateObject),
            diff = dayOfWeek >= firstDayOfWeekIndex ?
                dayOfWeek - firstDayOfWeekIndex :
                6 - dayOfWeek

        firstDayOfWeek.setDate(dateObject.getDate() - diff)
        firstDayOfWeek.setHours(0,0,0,0)

        return firstDayOfWeek
    }

    function keydown_handler(event) {
        if($settings.day_switch_keys) {
            if(event.key === "ArrowLeft") {
                event.preventDefault();
                change_day(-7);
            } else if(event.key === "ArrowRight") {
                event.preventDefault();
                change_day(7);
            }
        }
    }

    function update_date_btns() {
        // TODO: Week logic somehow
        /*let valid_prev_date = get_valid_date(date, -1);
        left_key_default_plan = valid_prev_date && enabled_dates.indexOf(valid_prev_date) === -1;
        show_left_key = !!valid_prev_date;
        right_key_default_plan = enabled_dates.indexOf(date) === -1 || enabled_dates.indexOf(date) === enabled_dates.length - 1;
        show_right_key = true;*/
    }

    onMount(() => {
        if(!school_num) {
            replace_page('school_manager');
        }
        title.set("Wochenplan");
    });

    let test_rooms_data = {
        "free_rooms_by_block": {
            "1": [
                "1"
            ]
        }
    };

    const plan_type_map = {
        "forms": "Klasse",
        "rooms": "Raum",
        "teachers": "Lehrer"
    };

    let preferences_apply = true;

    $: block_config_obj = new BlockConfiguration(block_config);


    // Update visibility of date switching buttons
    $: date && enabled_dates && update_date_btns();
    // Update location hash
    $: school_num, date, plan_type, plan_value, (() => {
        if(location.hash === "#weekplan") {
            replace_hash(gen_location_hash("weekplan", school_num, date, plan_type, plan_value))
            return;
        }
        update_hash(gen_location_hash("weekplan", school_num, date, plan_type, plan_value));
    })();

    $: date, week_dates = [0, 1, 2, 3, 4].map((offset) => {
        let tmp_date = new Date(date);
        tmp_date.setDate(tmp_date.getDate() + offset);
        return `${tmp_date.getFullYear()}-${pad(tmp_date.getMonth()+1)}-${pad(tmp_date.getDate())}`;
    })
</script>

<svelte:window on:keydown={keydown_handler}/>

{#if !plan_type}
    <span class="responsive-text">Wähle eine Klasse, einen Lehrer, einen Raum oder die Raumübersicht aus, um einen Plan zu sehen.</span>
{:else}
    <div class="plan">
        {#if week_type && plan_type && plan_value}
            {#if plan_type === "forms" && ($selected_favorite !== -1)}
                <button on:click={() => {preferences_apply = !preferences_apply}} class="plus-btn">{preferences_apply ? "Alle Stunden anzeigen" : "Nur ausgewählte anzeigen"}</button>
            {/if}
            <h1 class="plan-heading">
                Woche für {plan_type_map[plan_type]} <span class="custom-badge">{plan_value}{#if plan_type === "teachers"}{#if full_teacher_name !== null}{` (${full_teacher_name})`}{/if}{/if}</span> vom <span class="custom-badge">{format_date(date)}</span> <span class="no-linebreak">{#if week_type}({week_type}-Woche){/if}</span>
            </h1>
        {/if}

        {#if plan_type === "room_overview"}
            <button on:click={() => {used_rooms_hidden = !used_rooms_hidden}} class="plus-btn">{used_rooms_hidden ? "Besetzte Räume anzeigen" : "Nur freie Räume anzeigen"}</button>
            {#if week_type}
                <h1 class="plan-heading">Freie Räume in der Woche vom <span class="custom-badge">{format_date(date)}</span> <span class="no-linebreak"/>({week_type}-Woche)</h1>
            {/if}
        {/if}

        <div class="week">
            <div class="time-indicators" class:hidden={plan_type === "room_overview"}>
                <div class="block-col">
                    {#each block_config_obj.iterBlocks() as block_number}
                        <span>{block_number}</span>
                    {/each}
                </div>
                <div class="lesson-col">
                    {#each block_config_obj.iterPeriods() as period_number}
                        <span>{period_number}</span>
                    {/each}
                </div>
            </div>
            {#each week_dates as week_date, i}
                <Day
                    first={i === 0}
                    last={i === week_dates.length-1}
                    bind:school_num
                    bind:plan_type
                    bind:plan_value
                    bind:all_rooms
                    bind:full_teacher_name
                    bind:teacher_contact_link
                    bind:teacher_image_path
                    bind:used_rooms_hidden
                    bind:week_letter={week_type}
                    bind:preferences_apply
                    enabled_dates={enabled_dates}
                    free_days={free_days}
                    date={week_date}
                    block_count={5}
                    meta={meta} />
            {/each}
        </div>
    </div>
{/if}

<div class="day-controls">
    <button tabindex="-1" on:click={() => {change_day(-7);}} class:hidden={!show_left_key}><span class="material-symbols-outlined left">arrow_back_ios_new</span></button>
    <button tabindex="-1" on:click={() => {change_day(7);}} class:hidden={!show_right_key}><span class="material-symbols-outlined right">arrow_forward_ios</span></button>
</div>

<style lang="scss">
  .week {
    --lesson-height: 5.2rem;
    @media only screen and (max-width: 900px) {
        --lesson-height: 4rem;
    }
    display: flex;
    flex-direction: row;
    border-radius: .5rem;

    width: 100%;
    overflow-x: auto;

    .time-indicators {
      display: flex;
      flex-direction: row;
      gap: 0.5rem;
      margin-right: 0.5rem;
      @media only screen and (max-width: 900px) {
        margin-top: calc(var(--font-size-base) + .8rem);
      }
      margin-top: calc(var(--font-size-lg) + .8rem);

      &.hidden {
        display: none;
      }

      .block-col {
        display: flex;
        flex-direction: column;

        span {
          height: calc(2 * var(--lesson-height) + .5rem);
          line-height: calc(2 * var(--lesson-height) + .5rem);
          font-weight: bold;
          font-size: var(--font-size-lg);
          @media only screen and (max-width: 900px) {
            font-size: var(--font-size-base);
          }
          text-align: center;
        }
      }

      .lesson-col {
        display: flex;
        flex-direction: column;

        span {
          font-size: var(--font-size-base);
          @media only screen and (max-width: 900px) {
            font-size: var(--font-size-sm);
          }
          height: calc(var(--lesson-height) + .25rem);
          line-height: calc(var(--lesson-height) + .25rem);
          opacity: 0.5;
          text-align: center;
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