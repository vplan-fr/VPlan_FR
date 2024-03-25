<script>
    import Dropdown from "../../base_components/Dropdown.svelte";
    import {active_modal, selected_favorite, settings, inspecting_lesson, inspecting_plan_type} from "../../stores.js";
    import {arraysEqual} from "../../utils.js";

    export let lesson;
    export let plan_type;
    export let plan_value;

    $: only_teacher_absent = lesson.scheduled_teachers?.length !== 0 && lesson.current_teachers?.length === 0 && lesson.takes_place;

    $: teachers = (lesson.takes_place && !only_teacher_absent ? lesson.current_teachers : lesson.scheduled_teachers) || [];
    $: s_teachers = (!arraysEqual(lesson.scheduled_teachers, teachers) ? lesson.scheduled_teachers?.filter(t => !teachers.includes(t)) : []) || [];

    $: forms = (lesson.takes_place ? lesson.current_forms : lesson.scheduled_forms) || [];
    $: s_forms = (!arraysEqual(lesson.scheduled_forms, forms) ? lesson.scheduled_forms?.filter(f => !forms.includes(f)) : []) || []
    $: forms_str = lesson.takes_place ? lesson.current_forms_str : lesson.scheduled_forms_str;
    $: s_forms_str = s_forms.length !== 0 ? lesson.scheduled_forms_str : "";

    $: rooms = (lesson.takes_place ? lesson.current_rooms : lesson.scheduled_rooms) || [];
    $: s_rooms = (!arraysEqual(lesson.scheduled_rooms, rooms) ? lesson.scheduled_rooms?.filter(r => !rooms.includes(r)) : []) || [];

    $: subject_changed = lesson.subject_changed && lesson.takes_place && !lesson.is_unplanned;
    $: teacher_changed = lesson.teacher_changed && lesson.takes_place && !lesson.is_unplanned;
    $: room_changed = lesson.room_changed && lesson.takes_place && !lesson.is_unplanned;
    $: forms_changed = lesson.forms_changed && lesson.takes_place && !lesson.is_unplanned;
</script>

<div class="card" class:filled_in_weekplan={$settings.filled_in_weekplan} class:cancelled={!lesson.takes_place} class:changed={lesson.is_unplanned}>
    {#if (lesson.info.length > 0) || (plan_type === "forms" && (forms.length > 1)) || (plan_type === "teachers" && (teachers.length > 1)) || (plan_type === "rooms" && (rooms.length > 1))}
        <button class="info-btn" on:click={() => {
            $active_modal = "lesson-inspect";
            $inspecting_lesson = lesson;
            $inspecting_plan_type = plan_type;
        }}>
            <span class="material-symbols-outlined">info</span>
        </button>
    {/if}
    <div class="vertical-align" style="height: 100%;">
        <!-- Subject -->
        <div class="subject extra_padding" class:changed={subject_changed} class:changed_filled_in={$settings.filled_in_buttons && subject_changed}>
            {#if lesson.scheduled_class == null && lesson.current_class == null}
                -
            {:else}
                {lesson.current_class != null ? lesson.current_class : ""}
                {#if lesson.takes_place}
                    {#if lesson.scheduled_class !== lesson.current_class && lesson.scheduled_class != null}
                        {#if lesson.current_class != null}&nbsp;{/if}
                        <s>{lesson.scheduled_class}</s>
                    {/if}
                {:else}
                    {lesson.scheduled_class}
                {/if}
            {/if}
        </div>
        <!-- Teachers -->
        {#if plan_type !== "teachers"}
            <div class="teachers info-element" class:changed={teacher_changed} class:changed_filled_in={$settings.filled_in_buttons && teacher_changed}
                 class:teacher_absent={only_teacher_absent} class:cancelled_filled_in={$settings.filled_in_buttons && only_teacher_absent}>
                {#if teachers.length !== 0 || s_teachers.length !== 0}
                    {#each teachers || [] as teacher}
                        <button on:click={() => {
                            plan_type = "teachers";
                            plan_value = teacher;
                            selected_favorite.set(-1);
                        }}>{teacher}</button>
                    {/each}
                    {#each s_teachers || [] as teacher}
                        <button on:click={() => {
                            plan_type = "teachers";
                            plan_value = teacher;
                            selected_favorite.set(-1);
                        }}><s>{teacher}</s></button>
                    {/each}
                {:else}
                    <span class="extra_padding">-</span>
                {/if}
            </div>
        {/if}
        <!-- Rooms -->
        {#if plan_type !== "rooms"}
            <div class="rooms horizontal-align info-element" class:changed={room_changed} class:changed_filled_in={$settings.filled_in_buttons && room_changed}>
                {#if rooms.length !== 0 || s_rooms.length !== 0}
                    {#each rooms || [] as room}
                        <button on:click={() => {
                            plan_type = "rooms";
                            plan_value = room;
                            selected_favorite.set(-1);
                        }}>{room}</button>
                    {:else}
                        <span class="extra_padding">-</span>
                    {/each}
                    {#each s_rooms || [] as room}
                        <button on:click={() => {
                            plan_type = "rooms";
                            plan_value = room;
                            selected_favorite.set(-1);
                        }}><s>{room}</s></button>
                    {/each}
                {:else}
                    <span class="extra_padding">-</span>
                {/if}
            </div>
        {/if}
        <!-- Forms -->
        {#if plan_type !== "forms"}
            {#if forms.length === 0 && s_forms.length === 0}
                <div class="forms info-element vertical-align" class:changed={forms_changed}>
                    <span class="extra_padding">-</span>
                </div>
            {:else if forms.length === 1 && s_forms.length === 0}
                <div class="forms info-element vertical-align" class:changed={forms_changed}>
                    <button on:click={() => {
                    plan_type = "forms";
                    plan_value = forms[0];
                    selected_favorite.set(-1);
                }}>{forms[0]}</button>
                </div>
            {:else if forms.length === 0 && s_forms.length === 1}
                <div class="forms info-element vertical-align" class:changed={forms_changed}>
                    <button on:click={() => {
                    plan_type = "forms";
                    plan_value = s_forms[0];
                    selected_favorite.set(-1);
                }}><s>{s_forms[0]}</s></button>
                </div>
            {:else}
                <div class="form-dropdown-wrapper">
                    <Dropdown small={true} transform_origin_x="50%">
                        <button slot="toggle_button" let:toggle on:click={toggle} class="toggle-button center-align" class:changed={forms_changed}>
                            <span class="grow">{forms_str}&nbsp;<s>{s_forms_str}</s></span>
                            <span class="material-symbols-outlined dropdown-arrow centered_txt">arrow_drop_down</span>
                        </button>

                        {#each forms as form}
                            <button on:click={() => {
                            plan_type = "forms";
                            plan_value = form;
                            selected_favorite.set(-1);
                        }}>{form}</button>
                        {/each}
                        {#each s_forms as form}
                            <button on:click={() => {
                            plan_type = "forms";
                            plan_value = form;
                            selected_favorite.set(-1);
                        }}><s>{form}</s></button>
                        {/each}
                    </Dropdown>
                </div>
            {/if}
        {/if}
    </div>
</div>
<style lang="scss">
  .info-btn {
    overflow: hidden;
    --padding: .2rem;
    position: absolute;
    top: 0;
    right: 0;
    transform: translate(30%, -20%);
    z-index: 1;
    padding: var(--padding);
    background: var(--background);

    &::before {
      content: "";
      background: rgba(255, 255, 255, 0.2);
      position: absolute;
      inset: 0;
    }

    border: none;
    height: calc(var(--card-font-size) + var(--padding) * 2);
    width: calc(var(--card-font-size) + var(--padding) * 2);
    line-height: var(--card-font-size);
    border-radius: 9vw;

    .material-symbols-outlined {
      font-size: var(--card-font-size);
      padding: 0;
      color: var(--text-color);
    }
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

  .form-dropdown-wrapper .dropdown-wrapper button {
    &.toggle-button {
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 5px;
      overflow: hidden;
      text-align: left;
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

    border: none;
    background: transparent;
    color: var(--text-color);
    transition: background-color .2s ease;
    width: 100%;
    font-size: inherit;

    &:hover, &:focus-visible {
      background-color: rgba(0, 0, 0, 0.5);
    }
  }

  .horizontal-align {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: .3em;
  }

  .info-element {
    display: flex;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 5px;

    &.teacher_absent {
      background: rgba(255, 255, 255, 0.08);
      outline: 1.5px solid var(--cancelled-color);
      outline-offset: -1.5px;
    }

    & > button {
      border-radius: 0;
      &:nth-of-type(1) {
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
      }
      &:nth-last-of-type(1) {
        border-bottom-left-radius: 5px;
        border-bottom-right-radius: 5px;
      }
    }
  }

  .changed {
    outline: solid 1.5px var(--accent-color);
    outline-offset: -1.5px;
  }

  .changed_filled_in {
    background: var(--accent-color) !important;
  }

  .subject,
  .teachers button,
  .rooms button,
  .forms button {
    color: var(--text-color);
    font-size: inherit;
    font-weight: 400;
    border: none;
    padding: .1rem .3rem;
    background: none;
    text-align: center;
    border-radius: 5px;
    line-height: normal;
  }

  .subject {
    white-space: nowrap;
  }

  .extra_padding {
    padding: .05rem .5rem;
    line-height: normal;
  }

  .rooms.horizontal-align {
    gap: 0;
  }

  .teachers button, .rooms button, .forms button {
    flex: 1;
    transition: background-color .2s ease;

    &:hover, &:focus-visible {
      background: rgba(255, 255, 255, 0.08);
    }
  }

  .teachers button {
    font-weight: 600;
  }

  .cancelled {
    outline: var(--cancelled-color) solid 1.5px;
    outline-offset: -1.5px;
  }

  .cancelled_filled_in {
    background: var(--cancelled-color) !important;
  }

  .vertical-align {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: .1rem;
  }

  .card {
    --card-font-size: var(--font-size-sm);
    @media only screen and (max-width: 900px) {
      --card-font-size: 0.6rem;
    }
    position: relative;
    background: var(--background);
    border-radius: .5rem;
    height: 100%;
    min-width: 4rem;
    padding: .2rem .4rem;
    box-sizing: border-box;
    font-size: var(--card-font-size);

    &.filled_in_weekplan {
        flex: 1;
    }

    &::before {
      content: "";
      pointer-events: none;
      position: absolute;
      inset: 0;
      z-index: 0;
      border-radius: .5rem;
      background: rgba(255, 255, 255, 0.05);
    }
  }
</style>