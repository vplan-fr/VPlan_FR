<script>
    import Dropdown from "../base_components/Dropdown.svelte";
    import {selected_favorite, settings} from "../stores";
    import {arraysEqual} from "../utils.js";

    export let lesson;
    export let date;
    export let plan_type;
    export let plan_value;
    export let display_time = true;

    function periods_to_block_label(periods) {
        periods.sort(function (a, b) {
            return a - b;
        });

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

<div class="card" class:cancelled={!lesson.takes_place} class:changed={lesson.is_unplanned}>
    <div class="horizontal-align">
        <!-- Optional: Time -->
        {#if display_time}
            <div class="vert-align max-width-center lesson-time-info">
                <span class="lesson-period">{periods_to_block_label(lesson.periods)}</span>
                <span class="lesson-time">{lesson.begin}</span>
            </div>
        {/if}
        <!-- Subject -->
        <div class="subject info-element max-width-center extra_padding" class:changed={subject_changed} class:changed_filled_in={$settings.filled_in_buttons && subject_changed}>
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
            <div class="teachers vert-align max-width-center info-element first_half" class:changed={teacher_changed} class:changed_filled_in={$settings.filled_in_buttons && teacher_changed}
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
            <div class="rooms vert-align max-width-center info-element" class:changed={room_changed} class:changed_filled_in={$settings.filled_in_buttons && room_changed}>
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
                <div class="forms max-width-center info-element vert-align" class:changed={forms_changed}>
                    <span class="extra_padding">-</span>
                </div>
            {:else if forms.length === 1 && s_forms.length === 0}
            <div class="forms max-width-center info-element vert-align" class:changed={forms_changed}>
                <button on:click={() => {
                    plan_type = "forms";
                    plan_value = forms[0];
                    selected_favorite.set(-1);
                }}>{forms[0]}</button>
            </div>
            {:else if forms.length === 0 && s_forms.length === 1}
            <div class="forms max-width-center info-element vert-align" class:changed={forms_changed}>
                <button on:click={() => {
                    plan_type = "forms";
                    plan_value = s_forms[0];
                    selected_favorite.set(-1);
                }}><s>{s_forms[0]}</s></button>
            </div>
            {:else}
            <div class="max-width">
                <Dropdown let:toggle small={true} transform_origin_x="50%">
                    <button slot="toggle_button" on:click={toggle} class="toggle-button center-align" class:changed={forms_changed}>
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
    <!-- Additional Infos -->
    {#if (lesson.info.length > 0) || (plan_type === "forms" && (forms.length > 1)) || (plan_type === "teachers" && (teachers.length > 1)) || (plan_type === "rooms" && (rooms.length > 1))}
        <div class="info-element lesson-info">
            <ul>
                {#each lesson.info as info_paragraph}
                    {#each info_paragraph as info_message}
                        <li>
                            <div class="horizontal_wrapper">
                                {#each info_message.text_segments as text_segment}
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
                                        <button class="no-btn-visuals">{text_segment.text}</button>
                                    {/if}
                                {/each}
                            </div>
                        </li>
                    {/each}
                {/each}
                {#if plan_type === "forms" && (forms.length > 1)}
                <li>
                    <div class="horizontal_wrapper">
                        Beteiligte Klassen:
                        <div class="fit-content-width">
                            <Dropdown let:toggle small={true} transform_origin_x="50%">
                                <button slot="toggle_button" on:click={toggle} class="toggle-button">
                                    <span class="grow">{forms_str}</span>
                                    <span class="material-symbols-outlined dropdown-arrow">arrow_drop_down</span>
                                </button>
                                
                                {#each forms as form}
                                    <button on:click={() => {
                                        plan_type = "forms";
                                        plan_value = form;
                                    }}>{form}</button>
                                {/each}
                            </Dropdown>
                        </div>
                    </div>
                </li>
                {/if}
                {#if plan_type === "teachers" && (teachers.length > 1)}
                <li>
                    <div class="horizontal_wrapper">
                        Beteiligte Lehrer:
                        <div class="fit-content-width">
                            <Dropdown let:toggle small={true} transform_origin_x="50%">
                                <button slot="toggle_button" on:click={toggle} class="toggle-button">
                                    <span class="grow">{teachers.join(', ')}</span>
                                    <span class="material-symbols-outlined dropdown-arrow">arrow_drop_down</span>
                                </button>
                                
                                {#each teachers as teacher}
                                    <button on:click={() => {
                                        plan_type = "teachers";
                                        plan_value = teacher;
                                    }}>{teacher}</button>
                                {/each}
                            </Dropdown>
                        </div>
                    </div>
                </li>
                {/if}
                {#if plan_type === "rooms" && (rooms.length > 1)}
                <li>
                    <div class="horizontal_wrapper">
                        In Räumen:
                        <div class="fit-content-width">
                            <Dropdown let:toggle small={true} transform_origin_x="50%">
                                <button slot="toggle_button" on:click={toggle} class="toggle-button">
                                    <span class="grow">{rooms.join(', ')}</span>
                                    <span class="material-symbols-outlined dropdown-arrow">arrow_drop_down</span>
                                </button>
                                
                                {#each rooms as room}
                                    <button on:click={() => {
                                        plan_type = "rooms";
                                        plan_value = room;
                                        selected_favorite.set(-1);
                                    }}>{room}</button>
                                {/each}
                            </Dropdown>
                        </div>
                    </div>
                </li>
                {/if}
            </ul>
        </div>
    {/if}
</div>
<style lang="scss">
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

    .max-width {
        width: 100%;
    }

    .fit-content-width .dropdown-wrapper button, .max-width .dropdown-wrapper button {
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
            font-size: 0.875rem;
            line-height: 1.313rem;
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
        padding: 5px;
        font-size: inherit;
        line-height: 1.313;

        &:hover, &:focus-visible {
            background-color: rgba(0, 0, 0, 0.5);
        }
    }

    .no-btn-visuals {
        border: 0;
        background: none;
        padding: 0;
        margin: 0;
        text-align: start;
    }

    .horizontal_wrapper {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: .3em;
    }

    .lesson-info {
        margin-top: 10px;
        padding: 8px !important;
        background: rgba(255, 255, 255, 0.05) !important;
        ul {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        min-height: unset !important;
        font-weight: 300;

        button {
            font-weight: inherit;
            font-size: 0.875rem;
            line-height: 1.313rem;
            color: var(--text-color);
        }

        .clickable {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 5px;
            padding: 0px 5px;
            transition: background-color 0.2s ease;

            &:hover, &:focus-visible {
                background-color: rgba(255, 255, 255, 0.2);
            }
        }

        .fit-content-width .dropdown-wrapper button, .max-width .dropdown-wrapper button {
            padding: 2px 0px 2px 5px;
        }
    }

    .info-element {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 5px;
        min-height: 1.943rem;

        &.teacher_absent {
            background: rgba(255, 255, 255, 0.08);
            outline: 3px solid var(--cancelled-color);
            outline-offset: -3px;
        }

        & > button {
            border-radius: 0px;
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

    .extra_padding {
        padding: 5px 0px;
        line-height: 1.313rem;
        min-height: 1.313rem;
    }

    .changed {
        outline: solid 3px var(--accent-color);
        outline-offset: -3px;
    }

    .changed_filled_in {
        background: var(--accent-color) !important;
    }

    .subject,
    .teachers button,
    .rooms button,
    .forms button {
        color: var(--text-color);
        font-weight: 400;
        border: none;
        background: none;
        width: 100%;
        height: 100%;
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

    .lesson-period {
        white-space: nowrap;
    }

    .lesson-period {
        font-size: 0.875rem;
        font-weight: 400;
    }

    .lesson-time {
        font-size: 0.75rem;
        font-weight: 400;
    }

    .subject,
    .info-element,
    .info-element>button,
    .extra_padding {
        font-size: 0.875rem;
    }

    .cancelled {
        outline: var(--cancelled-color) solid 3px;
        outline-offset: -3px;
    }

    .cancelled_filled_in {
        background: var(--cancelled-color) !important;
    }

    .horizontal-align {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        gap: 8vw;

        @media only screen and (max-width: 380px) {
            gap: 5px;
        }
    }

    .vert-align {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .max-width-center {
        width: 100%;
        display: flex;
        justify-content: center;
        box-sizing: border-box;
    }

    .card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 5px;
        padding: 10px;

        .lesson-time-info {
            gap: 5px;
        }
    }

    // Desktop View Styles

    .grid-align-wrapper {
       width: 100%;
       display: grid;
       grid-template-columns: repeat(2, 1fr);
       grid-template-rows: min-content min-content;
       &.large_grid {
           grid-template-rows: min-content min-content min-content;
       }
       grid-column-gap: 10px;
       grid-row-gap: 10px;
       .wide-area {
           grid-area: 1 / 1 / 2 / 3;
           &.second_of_type {
               grid-area: 3 / 1 / 4 / 3;
           }
       }
       .small-area {
           grid-area: 2 / 1 / 3 / 2;
           &.second_of_type {
               grid-area: 2 / 2 / 3 / 3;
           }
       }
    }
</style>