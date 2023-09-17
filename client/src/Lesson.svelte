<script>
    import Dropdown from "./Components/Dropdown.svelte";
    import {settings} from "./stores";

    export let lesson;
    export let date;
    export let plan_type;
    export let plan_value;
    export let display_time = true;

    $: teacher_absent = lesson.scheduled_teachers?.length !== 0 && lesson.current_teachers.length === 0 && lesson.takes_place;
    $: teachers = (lesson.takes_place && !teacher_absent ? lesson.current_teachers : lesson.scheduled_teachers) || [];
    $: forms = (lesson.takes_place ? lesson.current_forms : lesson.scheduled_forms) || [];
    $: forms_str = lesson.takes_place ? lesson.current_forms_str : lesson.scheduled_forms_str;
    $: rooms = (lesson.takes_place ? lesson.current_rooms : lesson.scheduled_rooms) || [];
    $: subject_changed = lesson.subject_changed && lesson.takes_place;
    $: teacher_changed = lesson.teacher_changed && lesson.takes_place;
    $: room_changed = lesson.room_changed && lesson.takes_place;
    // $: form_changed = lesson.form_changed && lesson.takes_place;

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
    //$: console.log(lesson);
</script>
<!-- Desktop View -->
<div class="card desktop-view" class:cancelled={!lesson.takes_place}>
    <div class="horizontal-align">
        <!-- Optional: Time -->
        {#if display_time}
        <div class="vert-align lesson-time-info">
            <span class="lesson-time">{lesson.begin}</span>
            <span class="lesson-period">{periods_to_block_label(lesson.periods)}</span>
            <span class="lesson-time">{lesson.end}</span>
        </div>
        {/if}
        <div class="grid-align-wrapper" class:large_grid={plan_type !== "forms"}>
            <!-- Subject -->
            <div class="subject max-width-center wide-area extra_padding" class:changed={subject_changed} class:changed_filled_in={$settings.filled_in_buttons && subject_changed}>
                {lesson.current_class != null ? lesson.current_class : ""}
                {#if lesson.takes_place}
                    {#if lesson.scheduled_class !== lesson.current_class && lesson.scheduled_class != null}
                        {#if lesson.current_class != null}&nbsp;{/if}
                        <s>{lesson.scheduled_class}</s>
                    {/if}
                {:else}
                    {lesson.scheduled_class}
                {/if}
                {#if lesson.scheduled_class == null && lesson.current_class == null}-{/if}
            </div>
            <!-- Teachers -->
            <div class="small-area vert-align">
                <div class="teachers vert-align max-width-center info-element first_half" class:changed={teacher_changed} class:changed_filled_in={$settings.filled_in_buttons && teacher_changed}
                    class:teacher_absent={teacher_absent} class:cancelled_filled_in={$settings.filled_in_buttons && teacher_absent}>
                    {#each teachers as teacher}
                        <button on:click={() => {
                            plan_type = "teachers";
                            plan_value = teacher;
                        }}>{teacher}</button>
                    {:else}
                        <span class="extra_padding">-</span>
                    {/each}
                </div>
            </div>
            <!-- Rooms -->
            <div class="rooms vert-align max-width-center info-element small-area second_of_type" class:changed={room_changed} class:changed_filled_in={$settings.filled_in_buttons && room_changed}>
                {#each rooms as room}
                    <button on:click={() => {
                        plan_type = "rooms";
                        plan_value = room;
                    }}>{room}</button>
                {:else}
                    <span class="extra_padding">-</span>
                {/each}
            </div>
            <!-- Forms -->
            {#if plan_type !== "forms"}
                {#if forms.length === 0}
                    <div class="forms max-width-center wide-area second_of_type info-element">
                        <span class="extra_padding">-</span>
                    </div>
                {:else if forms.length === 1}
                <div class="forms max-width-center wide-area second_of_type info-element">
                    <button on:click={() => {
                        plan_type = "forms";
                        plan_value = forms[0];
                    }}>{forms[0]}</button>
                </div>
                {:else}
                <div class="forms max-width wide-area second_of_type">
                    <Dropdown let:toggle small_version={true} transform_origin_x="50%">
                        <button slot="toggle_button" on:click={toggle} class="toggle-button center-align">
                            <span class="grow">{forms_str}</span>
                            <span class="material-symbols-outlined dropdown-arrow centered_txt">arrow_drop_down</span>
                        </button>
                        
                        {#each forms as form}
                            <button on:click={() => {
                                plan_type = "forms";
                                plan_value = form;
                            }}>{form}</button>
                        {/each}
                    </Dropdown>
                </div>
                {/if}
            {/if}
        </div>
    </div>
    <!-- Additional Infos -->
    {#if (lesson.info.length > 0) || (plan_type === "forms" && (forms.length > 1))}
        <div class="info-element lesson-info">
            <ul>
                {#each lesson.info as elem}
                    {#each elem as element}
                        <li>
                            {#each element.text_segments as text_segment}
                                {#if text_segment.link !== null}
                                    <button class="no-btn-visuals" on:click={() => {
                                        date = text_segment.link.date;
                                        plan_type = text_segment.link.type;
                                        plan_value = text_segment.link.value;
                                    }}>
                                        <div class="clickable">{text_segment["text"]}</div>
                                    </button>
                                {:else}
                                    <button class="no-btn-visuals">{text_segment["text"]}</button>
                                {/if}
                            {/each}
                        </li>
                    {/each}
                {/each}
                {#if plan_type === "forms" && (forms.length > 1)}
                <li>
                    <div class="horizontal_wrapper">
                        Beteiligte Klassen:
                        <div class="fit-content-width">
                            <Dropdown let:toggle small_version={true} transform_origin_x="50%">
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
            </ul>
        </div>
    {/if}
</div>
<!-- Mobile View -->
<div class="card mobile-view" class:cancelled={!lesson.takes_place}>
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
            {lesson.current_class != null ? lesson.current_class : ""}
            {#if lesson.takes_place}
                {#if lesson.scheduled_class !== lesson.current_class && lesson.scheduled_class != null}
                    {#if lesson.current_class != null}&nbsp;{/if}
                    <s>{lesson.scheduled_class}</s>
                {/if}
            {:else}
                {lesson.scheduled_class}
            {/if}
            {#if lesson.scheduled_class == null && lesson.current_class == null}-{/if}
        </div>
        <!-- Teachers -->
        {#if plan_type !== "teachers"}
            <div class="teachers vert-align max-width-center info-element first_half" class:changed={teacher_changed} class:changed_filled_in={$settings.filled_in_buttons && teacher_changed}
                 class:teacher_absent={teacher_absent} class:cancelled_filled_in={$settings.filled_in_buttons && teacher_absent}>
                {#each teachers as teacher}
                    <button on:click={() => {
                        plan_type = "teachers";
                        plan_value = teacher;
                    }}>{teacher}</button>
                {:else}
                    <span class="extra_padding">-</span>
                {/each}
            </div>
        {/if}
        <!-- Rooms -->
        <div class="rooms vert-align max-width-center info-element" class:changed={room_changed} class:changed_filled_in={$settings.filled_in_buttons && room_changed}>
            {#each rooms as room}
                <button on:click={() => {
                    plan_type = "rooms";
                    plan_value = room;
                }}>{room}</button>
            {:else}
                <span class="extra_padding">-</span>
            {/each}
        </div>
        <!-- Forms -->
        {#if plan_type !== "forms"}
            {#if forms.length === 0}
                <div class="forms max-width-center info-element vert-align">
                    <span class="extra_padding">-</span>
                </div>
            {:else if forms.length === 1}
            <div class="forms max-width-center info-element vert-align">
                <button on:click={() => {
                    plan_type = "forms";
                    plan_value = forms[0];
                }}>{forms[0]}</button>
            </div>
            {:else}
            <div class="max-width">
                <Dropdown let:toggle small_version={true} transform_origin_x="50%">
                    <button slot="toggle_button" on:click={toggle} class="toggle-button center-align">
                        <span class="grow">{forms_str}</span>
                        <span class="material-symbols-outlined dropdown-arrow centered_txt">arrow_drop_down</span>
                    </button>
                    
                    {#each forms as form}
                        <button on:click={() => {
                            plan_type = "forms";
                            plan_value = form;
                        }}>{form}</button>
                    {/each}
                </Dropdown>
            </div>
            {/if}
        {/if}
    </div>
    <!-- Additional Infos -->
    {#if (lesson.info.length > 0) || (plan_type === "forms" && (forms.length > 1))}
        <div class="info-element lesson-info">
            <ul>
                {#each lesson.info as elem}
                    {#each elem as element}
                        <li>
                            {#each element.text_segments as text_segment}
                                {#if text_segment.link !== null}
                                    <button class="no-btn-visuals" on:click={() => {
                                        date = text_segment.link.date;
                                        plan_type = text_segment.link.type;
                                        plan_value = text_segment.link.value;
                                    }}>
                                        <div class="clickable">{text_segment["text"]}</div>
                                    </button>
                                {:else}
                                    <button class="no-btn-visuals">{text_segment["text"]}</button>
                                {/if}
                            {/each}
                        </li>
                    {/each}
                {/each}
                {#if plan_type === "forms" && (forms.length > 1)}
                <li>
                    <div class="horizontal_wrapper">
                        Beteiligte Klassen:
                        <div class="fit-content-width">
                            <Dropdown let:toggle small_version={true} transform_origin_x="50%">
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
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            overflow: hidden;
            text-align: left;

            span.grow {
                flex: 1;
                white-space: nowrap;
            }
            
            &.center-align {
                text-align: center;
            }

            &:hover, &:focus-visible {
                background-color: rgba(255, 255, 255, 0.2);
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
        margin: 0 .3rem 0 0;
        text-align: start;
    }

    .horizontal_wrapper {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 10px;
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
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            padding: 0px 5px;
            transition: background-color 0.2s ease;

            &:hover, &:focus-visible {
                background-color: rgba(255, 255, 255, 0.2);
            }
        }
    }

    .info-element {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 5px;
        min-height: 1.938rem;

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
            background: rgba(255, 255, 255, 0.1);
        }
    }

    .teachers button {
        font-weight: 600;
    }

    .lesson-period {
        white-space: nowrap;
    }

    .mobile-view {
        display: none;
        @media only screen and (max-width: 1500px) {
           display: block;
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
    .desktop-view {
        .fit-content-width .dropdown-wrapper button, .max-width .dropdown-wrapper button {
            font-size: 1.875rem;
            &.toggle-button {
                border-radius: 8px;
            }
            padding: 16px;
            line-height: 1;
        }

        .no-btn-visuals {
            font-size: inherit;
            margin: 0 .3rem 0 0;
        }

        .horizontal_wrapper {
            gap: 20px;
        }

        .lesson-info {
            margin-top: 20px;
            padding: 15px !important;
            ul {
                gap: 8px;
            }

            .clickable {
                border-radius: 8px;
                padding: 10px;
            }
        }

        display: none;
        @media only screen and (min-width: 1501px) {
            display: block;
        }
        .horizontal-align {
            gap: 0;
            justify-content: space-between;
        }
        .lesson-time-info {
            padding: 0px 40px 0px 30px;
        }
        .info-element {
            line-height: 1;
            & > button {
                padding: 16px;
                line-height: 1;
                border-radius: 0px;
                &:nth-of-type(1) {
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
                &:nth-last-of-type(1) {
                    border-bottom-left-radius: 8px;
                    border-bottom-right-radius: 8px;
                }
            }
            border-radius: 8px;
        }

        .extra_padding {
            padding: 16px 0px;
            line-height: 1;
            border-radius: 8px;
        }
        .lesson-period {
            font-size: 1.625rem;
            font-weight: 400;
        }
        .lesson-time {
            font-size: 1.25rem;
            font-weight: 400;
        }
        .subject, .info-element, .info-element > button {
            font-size: 1.875rem;
        }
        .cancelled {
            grid-area: 1 / 1 / 3 / 3;
        }
        .forms, .rooms {
            flex-direction: column;
            align-items: center;
        }
    }
</style>