<script>
    import Dropdown from "./Dropdown.svelte";

    export let lesson;
    export let date;
    export let plan_type;
    export let plan_value;
    export let display_time = true;

    $: teacher_absent = lesson.scheduled_teachers?.length !== 0 && lesson.current_teachers.length === 0 && lesson.takes_place
    $: subject = (lesson.takes_place ? lesson.current_class : lesson.scheduled_class)
    $: teachers = (lesson.takes_place && !teacher_absent ? lesson.current_teachers : lesson.scheduled_teachers) || []
    $: forms = (lesson.takes_place ? lesson.current_forms : lesson.scheduled_forms) || []
    $: forms_str = lesson.takes_place ? lesson.current_forms_str : lesson.scheduled_forms_str
    $: rooms = (lesson.takes_place ? lesson.current_rooms : lesson.scheduled_rooms) || []
    $: subject_changed = lesson.subject_changed && lesson.takes_place
    $: teacher_changed = lesson.teacher_changed && lesson.takes_place
    $: room_changed = lesson.room_changed && lesson.takes_place

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
</script>
<!--<div class="card desktop-view">-->
<!--    <div class="horizontal-align">-->
<!--        {#if display_time}-->
<!--        <div class="vert-align lesson-time-info">-->
<!--            <span class="lesson-time">{lesson.begin}</span>-->
<!--            <span class="lesson-period">{periods_to_block_label(lesson.periods)}</span>-->
<!--            <span class="lesson-time">{lesson.end}</span>-->
<!--        </div>-->
<!--        {/if}-->
<!--        <div class="grid-align-wrapper" class:large_grid={plan_type !== "forms"}>-->
<!--            {#if lesson.current_subject !== "-&#45;&#45;"}-->
<!--            {#if lesson.current_subject !== null}-->
<!--            <div class="subject max-width-center wide-area extra_padding" class:changed={lesson.subject_changed}>-->
<!--                {lesson.current_subject}-->
<!--            </div>-->
<!--            {/if}-->
<!--            <div class="small-area vert-align">-->
<!--                <div class="teachers vert-align max-width-center info-element" class:changed={lesson.teacher_changed} class:teacher_absent={lesson.current_teacher === null}>-->
<!--                    <button on:click={() => {-->
<!--                        plan_type = "teachers";-->
<!--                        plan_value = lesson.current_teacher === null ? lesson.class_teacher : lesson.current_teacher;-->
<!--                    }}>{lesson.current_teacher === null ? lesson.class_teacher : lesson.current_teacher}</button>-->
<!--                </div>-->
<!--            </div>-->
<!--            <div class="rooms vert-align max-width-center info-element small-area second_of_type" class:changed={lesson.room_changed}>-->
<!--                {#each lesson.rooms as room}-->
<!--                    <button on:click={() => {-->
<!--                        plan_type = "rooms";-->
<!--                        plan_value = room;-->
<!--                    }}>{room}</button>-->
<!--                {:else}-->
<!--                    <span class="extra_padding">X</span>-->
<!--                {/each}-->
<!--            </div>-->
<!--            {:else}-->
<!--            <div class="max-width-center info-element cancelled vert-align changed">-->
<!--                <span class="extra_padding">X</span>-->
<!--            </div>-->
<!--            {/if}-->
<!--            {#if !(plan_type === "forms" && (lesson.forms.length === 1))}-->
<!--            <div class="forms max-width-center wide-area second_of_type info-element">-->
<!--                {#if lesson.forms.length === 1}-->
<!--                    <button on:click={() => {-->
<!--                        plan_type = "forms";-->
<!--                        plan_value = lesson.forms[0];-->
<!--                    }}>{lesson.forms[0]}</button>-->
<!--                {:else}-->
<!--                    <DropdownShell let:toggle class="dropdown-shell">-->
<!--                        <button on:click={toggle}>-->
<!--                            {lesson.forms_str}-->
<!--                        </button>-->
<!--                        <Dropdown>-->
<!--                            <div class="lighten_background">-->
<!--                                {#each lesson.forms as form}-->
<!--                                    <button on:click={() => {-->
<!--                                        plan_type = "forms";-->
<!--                                        plan_value = form;-->
<!--                                    }}>{form}</button>-->
<!--                                {/each}-->
<!--                            </div>-->
<!--                        </Dropdown>-->
<!--                    </DropdownShell>-->
<!--                {/if}-->
<!--            </div>-->
<!--            {/if}-->
<!--        </div>-->
<!--    </div>-->
<!--    {#if lesson.parsed_info.length > 0}-->
<!--        <div class="info-element lesson-info">-->
<!--            {#each lesson.parsed_info as elem}-->
<!--                <ul>-->
<!--                    {#each elem as element}-->
<!--                        <li>-->
<!--                            {#each element.text_segments as text_segment}-->
<!--                                <button class="no-btn-visuals" on:click={() => {-->
<!--                                    if(text_segment.link !== null) {-->
<!--                                        date = text_segment.link.date;-->
<!--                                        plan_type = text_segment.link.type;-->
<!--                                        plan_value = text_segment.link.value;-->
<!--                                    }-->
<!--                                }-->
<!--                                }>{text_segment["text"]}</button>-->
<!--                            {/each}-->
<!--                        </li>-->
<!--                    {/each}-->
<!--                </ul>-->
<!--            {/each}-->
<!--        </div>-->
<!--    {/if}-->
<!--</div>-->
<div class="card mobile-view" class:cancelled={!lesson.takes_place}>
    <div class="horizontal-align">
        {#if display_time}
            <div class="vert-align max-width-center lesson-time-info">
                <span class="lesson-period">{periods_to_block_label(lesson.periods)}</span>
                <span class="lesson-time">{lesson.begin}</span>
            </div>
        {/if}
        <div class="subject info-element max-width-center extra_padding" class:changed={subject_changed}>
            {lesson.current_class != null ? lesson.current_class : ""}
            {#if lesson.scheduled_class !== lesson.current_class && lesson.scheduled_class != null}
                {#if lesson.current_class != null}&nbsp;{/if}
                <s>{lesson.scheduled_class}</s>
            {/if}
            {#if lesson.scheduled_class == null && lesson.current_class == null}-{/if}
        </div>
        {#if plan_type !== "teachers"}
            {#if teachers.length === 0}
            <div class="teachers vert-align max-width-center info-element first_half" class:changed={teacher_changed}
                    class:teacher_absent={teacher_absent}>
                <span class="extra_padding">-</span>
            </div>
            {:else if teachers.length === 1}
            <div class="teachers vert-align max-width-center info-element first_half" class:changed={teacher_changed}
                    class:teacher_absent={teacher_absent}>
                <button on:click={() => {
                    plan_type = "teachers";
                    plan_value = teachers[0];
                }}>{teachers[0]}</button>
            </div>
            {:else}
            <div class="max-width">
                <Dropdown let:toggle small_version={true} transform_origin="50% 0%">
                    <button slot="toggle_button" on:click={toggle}>{teachers.join(" ")}</button>
                    
                    {#each teachers as teacher}
                        <button on:click={() => {
                            plan_type = "teachers";
                            plan_value = teacher;
                        }}>{teacher}</button>
                    {/each}
                </Dropdown>
            </div>
            {/if}
        {/if}
        <div class="rooms vert-align max-width-center info-element" class:changed={room_changed}>
            {#each rooms as room}
                <button on:click={() => {
                    plan_type = "rooms";
                    plan_value = room;
                }}>{room}</button>
            {:else}
                <span class="extra_padding">-</span>
            {/each}
        </div>

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
                <Dropdown let:toggle small_version={true} transform_origin="50% 0%">
                    <button slot="toggle_button" on:click={toggle} class="toggle-button">{forms_str}</button>
                    
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
    {#if lesson.info.length > 0}
        <div class="info-element lesson-info">
            {#each lesson.info as elem}
                <ul>
                    {#each elem as element}
                        <li>
                            {#each element.text_segments as text_segment}
                                {#if text_segment.link !== null}
                                    <button class="no-btn-visuals" on:click={() => {
                                        date = text_segment.link.date;
                                        plan_type = text_segment.link.type;
                                        plan_value = text_segment.link.value;
                                    }}>
                                        <u style="text-decoration: 2px underline solid var(--accent-color)">{text_segment["text"]}</u>
                                    </button>
                                {:else}
                                    <button class="no-btn-visuals">{text_segment["text"]}</button>
                                {/if}
                            {/each}
                        </li>
                    {/each}
                    {#if plan_type === "forms" && (forms.length > 1)}
                        <li>
                            <div class="horizontal_wrapper">
                                Beteiligte Klassen:
                                <div class="fit-content-width">
                                    <Dropdown let:toggle small_version={true} transform_origin="50% 0%">
                                        <button slot="toggle_button" on:click={toggle} class="toggle-button">{forms_str}</button>
                                        
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
            {/each}
        </div>
    {/if}
</div>
<style lang="scss">
    .fit-content-width {
        width: fit-content;
    }

    .max-width {
        width: 100%;
    }

    .fit-content-width .dropdown-wrapper button, .max-width .dropdown-wrapper button {
        &.toggle-button {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 5px;
            overflow: hidden;
        }

        border: none;
        background: transparent;
        color: var(--text-color);
        transition: background-color .2s ease;
        width: 100%;
        padding: 5px;
        font-size: inherit;
        line-height: 1.313;
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
        margin-top: 5px;
    }

    .lesson-info {
        margin-top: 10px;
        padding: 8px !important;
        background: rgba(255, 255, 255, 0.05) !important;
        display: flex;
        flex-direction: column;
        gap: 10px;
        min-height: unset !important;
        font-weight: 300;

        button {
            font-weight: inherit;
            font-size: 0.875rem;
            line-height: 1.313rem;
            color: var(--text-color);
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

    .teachers button {
        font-weight: 600;
    }

    .lesson-period {
        white-space: nowrap;
    }

    .mobile-view {
        //display: none;
        //@media only screen and (max-width: 600px) {
        //    display: block;
        //}
        display: block;

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
        outline-offset: -1.5px;
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
    }

    .card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 5px;
        padding: 10px;

        .lesson-time-info {
            gap: 5px;
        }
    }

    //:global(.desktop-view .info-element .dropdown-shell) {
    //    & > button {
    //        font-size: 1.875rem;
    //        padding: 1rem;
    //        line-height: 1;
    //        border-radius: 8px;
    //    }
    //}
    // :global(.desktop-view .info-element .dropdown) {
    //     border-radius: 0px 0px 8px 8px !important;

    //     button {
    //         font-size: 1.875rem;
    //         padding: 1rem;
    //         line-height: 1;

    //         &:nth-last-of-type(1) {
    //             border-bottom-left-radius: 8px;
    //             border-bottom-right-radius: 8px;
    //         }
    //     }
    // }
    //.grid-align-wrapper {
    //    width: 100%;
    //    display: grid;
    //    grid-template-columns: repeat(2, 1fr);
    //    grid-template-rows: min-content min-content;
    //    &.large_grid {
    //        grid-template-rows: min-content min-content min-content;
    //    }
    //    grid-column-gap: 10px;
    //    grid-row-gap: 10px;
    //    .wide-area {
    //        grid-area: 1 / 1 / 2 / 3;
    //        &.second_of_type {
    //            grid-area: 3 / 1 / 4 / 3;
    //        }
    //    }
    //    .small-area {
    //        grid-area: 2 / 1 / 3 / 2;
    //        &.second_of_type {
    //            grid-area: 2 / 2 / 3 / 3;
    //        }
    //    }
    //}
    //.desktop-view {
    //    display: none;
    //    @media only screen and (min-width: 601px) {
    //        display: block;
    //    }
    //    .horizontal-align {
    //        gap: 0;
    //        justify-content: space-between;
    //    }
    //    .lesson-time-info {
    //        padding: 0px 40px 0px 30px;
    //    }
    //    .subject {
    //        padding: .6rem 0;
    //    }
    //    .info-element {
    //        line-height: 1;
    //        & > button {
    //            padding: 1rem;
    //            line-height: 1;
    //            &:nth-of-type(1) {
    //                border-top-left-radius: 8px;
    //                border-top-right-radius: 8px;
    //            }
    //            &:nth-last-of-type(1) {
    //                border-bottom-left-radius: 8px;
    //                border-bottom-right-radius: 8px;
    //            }
    //        }
    //        border-radius: 8px;
    //    }
    //    .extra_padding {
    //        padding: 1rem 0rem;
    //        line-height: 1;
    //        border-radius: 8px;
    //    }
    //    .lesson-period {
    //        font-size: 1.625rem;
    //        font-weight: 400;
    //    }
    //    .lesson-time {
    //        font-size: 1.25rem;
    //        font-weight: 400;
    //    }
    //    .subject, .info-element, .info-element > button {
    //        font-size: 1.875rem;
    //    }
    //    .lesson-info {
    //        margin-top: 20px;
    //        button {
    //            font-size: 1.3rem;
    //            line-height: 1.5;
    //        }
    //    }
    //    .cancelled {
    //        grid-area: 1 / 1 / 3 / 3;
    //    }
    //    .forms, .rooms {
    //        flex-direction: column;
    //        align-items: center;
    //    }
    //}
</style>