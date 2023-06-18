<script>
    import { DropdownShell, Dropdown } from 'attractions';

    export let api_base;
    export let date;
    export let plan_type;
    export let plan_value;
    export let show_title;
    export let extra_height;
    let lessons = [];
    let info;
    let title = "";
    let loading = true;
    let plan_type_map = {
        "forms": "Klasse",
        "rooms": "Raum",
        "teachers": "Lehrer"
    }
    let controller = new AbortController();
    
    function load_lessons(date, plan_type, entity) {
        controller.abort();
        loading = true;
        title = `${plan_type}-plan for ${plan_type} ${entity}`;
        controller = new AbortController();
        fetch(`${api_base}/plan?date=${date}`, {signal: controller.signal})
            .then(response => response.json())
            .then(data => {
                loading = false;
                try {
                    lessons = data["plans"][plan_type][entity] || [];
                    info = data["info"];
                } catch {
                    lessons = []
                }
                console.log(lessons);
            })
            .catch(error => {
                console.error(error);
        });
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

    $: load_lessons(date, plan_type, plan_value);
</script>

<div class="plan" class:extra-height={extra_height}>
    <div class:loading>
        {#if show_title && info}
            <div class="responsive-heading">
                Plan für {plan_type_map[plan_type]} <span class="custom-badge">{plan_value}</span> am <span class="custom-badge">{date}</span> <span class="no-linebreak">({info.week}-Woche)</span>
            </div>
        {/if}
        {#if lessons.length == 0}
            {#if loading}
            Loading...
            {:else}
            No Lessons
            {/if}
        {/if}
        {#each lessons as lesson}
        <div class="card desktop-view">
            <div class="horizontal-align">
                <div class="vert-align lesson-time-info">
                    <span class="lesson-time">{lesson.begin}</span>
                    <span class="lesson-period">{periods_to_block_label(lesson.periods)}</span>
                    <span class="lesson-time">{lesson.end}</span>
                </div>
                <div class="grid-align-wrapper" class:large_grid={plan_type !== "forms"}>
                    {#if lesson.current_subject !== "---"}
                    {#if lesson.current_subject !== null}
                    <div class="subject max-width-center wide-area extra_padding" class:changed={lesson.subject_changed}>
                        {lesson.current_subject}
                    </div>
                    {/if}
                    <div class="small-area vert-align">
                        <div class="teachers vert-align max-width-center info-element" class:changed={lesson.teacher_changed} class:teacher_absent={lesson.current_teacher === null}>
                            <button on:click={() => {
                                plan_type = "teachers";
                                plan_value = lesson.current_teacher === null ? lesson.class_teacher : lesson.current_teacher;
                            }}>{lesson.current_teacher === null ? lesson.class_teacher : lesson.current_teacher}</button>
                        </div>
                    </div>
                    <div class="rooms vert-align max-width-center info-element small-area second_of_type" class:changed={lesson.room_changed}>
                        {#each lesson.rooms as room}
                            <button on:click={() => {
                                plan_type = "rooms";
                                plan_value = room;
                            }}>{room}</button>
                        {:else}
                            <span class="extra_padding">X</span>
                        {/each}
                    </div>
                    {:else}
                    <div class="max-width-center info-element cancelled vert-align changed">
                        <span class="extra_padding">X</span>
                    </div>
                    {/if}
                    {#if !(plan_type === "forms" && (lesson.forms.length === 1))}
                    <div class="forms max-width-center wide-area second_of_type info-element">
                        {#if lesson.forms.length === 1}
                            <button on:click={() => {
                                plan_type = "forms";
                                plan_value = lesson.forms[0];
                            }}>{lesson.forms[0]}</button>
                        {:else}
                            <DropdownShell let:toggle class="dropdown-shell">
                                <button on:click={toggle}>
                                    {lesson.forms_str}
                                </button>
                                <Dropdown>
                                    <div class="lighten_background">
                                        {#each lesson.forms as form}
                                            <button on:click={() => {
                                                plan_type = "forms";
                                                plan_value = form;
                                            }}>{form}</button>
                                        {/each}
                                    </div>
                                </Dropdown>
                            </DropdownShell>
                        {/if}
                    </div>
                    {/if}
                </div>
            </div>
            {#if lesson.parsed_info.length > 0}
                <div class="info-element lesson-info">
                    {#each lesson.parsed_info as elem}
                        <ul>
                            {#each elem as element}
                                <li>{element[0]}</li>
                            {/each}
                        </ul>
                    {/each}
                </div>
            {/if}
        </div>
        <div class="card mobile-view">
            <div class="horizontal-align">
                <div class="vert-align max-width-center lesson-time-info">
                    <span class="lesson-period">{periods_to_block_label(lesson.periods)}</span>
                    <span class="lesson-time">{lesson.begin}</span>
                </div>
                {#if lesson.current_subject !== "---"}
                <div class="subject max-width-center extra_padding" class:changed={lesson.subject_changed}>
                    {#if lesson.current_subject !== null}
                    {lesson.current_subject}
                    {/if}
                </div>
                <div class="teachers vert-align max-width-center info-element first_half" class:changed={lesson.teacher_changed} class:teacher_absent={lesson.current_teacher === null}>
                    <button on:click={() => {
                        plan_type = "teachers";
                        plan_value = lesson.current_teacher === null ? lesson.class_teacher : lesson.current_teacher;
                    }}>{lesson.current_teacher === null ? lesson.class_teacher : lesson.current_teacher}</button>
                </div>
                <div class="rooms vert-align max-width-center info-element" class:changed={lesson.room_changed}>
                    {#each lesson.rooms as room}
                        <button on:click={() => {
                            plan_type = "rooms";
                            plan_value = room;
                        }}>{room}</button>
                    {:else}
                        <span class="extra_padding">X</span>
                    {/each}
                </div>
                {:else}
                <div class="max-width-center info-element cancelled vert-align changed">
                    <span class="extra_padding">X</span>
                </div>
                {/if}
                {#if !(plan_type === "forms" && (lesson.forms.length === 1))}
                <div class="forms max-width-center info-element vert-align">
                    {#if lesson.forms.length === 1}
                        <button on:click={() => {
                            plan_type = "forms";
                            plan_value = lesson.forms[0];
                        }}>{lesson.forms[0]}</button>
                    {:else}
                        <DropdownShell let:toggle class="dropdown-shell">
                            <button on:click={toggle}>
                                {lesson.forms_str}
                            </button>
                            <Dropdown>
                                <div class="lighten_background">
                                    {#each lesson.forms as form}
                                        <button on:click={() => {
                                            plan_type = "forms";
                                            plan_value = form;
                                        }}>{form}</button>
                                    {/each}
                                </div>
                            </Dropdown>
                        </DropdownShell>
                    {/if}
                </div>
                {/if}
            </div>
            {#if lesson.parsed_info.length > 0}
                <div class="info-element lesson-info">
                    {#each lesson.parsed_info as elem}
                        <ul>
                            {#each elem as element}
                                <li>{element[0]}</li>
                            {/each}
                        </ul>
                    {/each}
                </div>
            {/if}
        </div>
        {/each}
        {#if info}
            <p class="additional-info">
                {#each info.additional_info as cur_info}
                    {#if cur_info !== null}
                        {cur_info}
                    {/if}
                    <br>
                {/each}
            </p>
            <span class="last-updated">Stand der Daten: <span class="custom-badge">{info.timestamp}</span></span>
        {/if}
    </div>
</div>

<style lang="scss">
    :global(.info-element .dropdown-shell) { 
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;

        & > button {
            transition: background-color .2s ease;
            width: 100%;
            padding: 5px;
            border-radius: 5px;
            width: 100%;
            line-height: 1.313rem;

            &:hover, &:focus-visible {
                background: rgba(0, 0, 0, 0.2) !important;
            }
        }
    }
    :global(.desktop-view .info-element .dropdown-shell) {
        & > button {
            font-size: 1.875rem;
            padding: 1rem;
            line-height: 1;
            border-radius: 8px;
        }
    }
    :global(.mobile-view .info-element .dropdown-shell > button) {
        font-size: 0.875rem;
    }
    :global(.info-element .dropdown) {
        width: 100%;
        top: calc(100% - 5px);
        border-radius: 0px 0px 5px 5px !important;
        margin-top: 0 !important;
        box-shadow: 0 4px 4px -1px rgba(0, 0, 0, 0.2), 0 5px 5px 0 rgba(0, 0, 0, 0.14), 0 10px 10px 0 rgba(0, 0, 0, 0.12) !important;
        background-color: var(--background-color) !important;
        overflow: hidden;
        .lighten_background {
            display: flex;
            flex-direction: column;
            background: rgba(255, 255, 255, 0.06);
    
            button {
                transition: background-color .2s ease;
                width: 100%;
                padding: 5px;
                &:nth-last-of-type(1) {
                    border-bottom-left-radius: 5px;
                    border-bottom-right-radius: 5px;
                }
                line-height: 1.313rem;
                &:hover, &:focus-visible {
                    background: rgba(0, 0, 0, 0.2) !important;
                }
            }
        }
    }
    :global(.mobile-view .info-element .dropdown) {
        button {
            font-size: 0.875rem;
            padding: 5px;
            line-height: normal;
        }
    }
    :global(.desktop-view .info-element .dropdown) {
        border-radius: 0px 0px 8px 8px !important;
        button {
            font-size: 1.875rem;
            padding: 1rem;
            line-height: 1;
            &:nth-last-of-type(1) {
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        }
    }

    .no-linebreak {
        white-space: nowrap;
    }
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
    .responsive-heading {
        font-size: clamp(1.063rem, 4vw, 2.28rem);
        line-height: clamp(1.406rem, 4.5vmax, 2.813rem);
        margin-bottom: 15px;
    }

    .custom-badge {
        background: rgba(255, 255, 255, 0.07);
        padding: 2px 7px;
        border-radius: 5px;
        white-space: nowrap;
    }

    .last-updated {
        margin: 16px 0px;
        font-size: clamp(0.875rem, 2.8vmin, 1.75rem);
    }

    .additional-info {
        margin-top: 20px;
        font-size: clamp(0.938rem, 3vmin, 1.875rem);
        line-height: 1.5;
    }

    .forms {
        font-size: 0.875rem;
    }

    .lesson-info {
        margin-top: 10px;
        padding: 8px !important;
        font-size: 0.875rem;
        font-weight: 300;
        line-height: 1.313rem;
        background: rgba(255, 255, 255, 0.05) !important;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .info-element {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 5px;
        min-height: 2rem;
        
        & > button {
            &:nth-of-type(1) {
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            &:nth-last-of-type(1) {
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            transition: background-color .2s ease;
            width: 100%;
            padding: 5px;
            line-height: 1.313rem;

            &:hover, &:focus-visible {
                background: rgba(0, 0, 0, 0.2) !important;
            }
        }
    
        &.teacher_absent {
            background: rgba(255, 255, 255, 0.08);
            outline: 3px solid var(--accent-color);
            outline-offset: -3px;
        }
    }

    .extra_padding {
        padding: 5px 0px;
        line-height: 1.313rem;
        min-height: 1.313rem;
    }
    
    .changed {
        background: var(--accent-color) !important;

        &:not(.teacher_absent) {
            & > button:hover, & > button:focus-visible {
                background: rgba(0, 0, 0, 0.3) !important;
            }
        }
    }

    .subject {
        border-radius: 5px;
    }

    .subject, .teachers button, .rooms button, .forms button {
        color: var(--text-color);
        font-weight: 400;
        border: none;
        background: none;
    }
    .teachers button {
        font-weight: 600;
    }
    .lesson-period {
        white-space: nowrap;
    }
    .mobile-view {
        display: none;
        @media only screen and (max-width: 600px) {
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
        .subject, .info-element, .info-element > button, .extra_padding {
            font-size: 0.875rem;
        }
        .cancelled {
            width: 400% !important;
        }
    }
    .desktop-view {
        display: none;
        @media only screen and (min-width: 601px) {
            display: block;
        }
        .horizontal-align {
            gap: 0;
            justify-content: space-between;
        }
        .lesson-time-info {
            padding: 0px 40px 0px 30px;
        }
        .subject {
            padding: .6rem 0;
        }
        .info-element {
            line-height: 1;
            & > button {
                padding: 1rem;
                line-height: 1;
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
            padding: 1rem 0rem;
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
        .lesson-info {
            font-size: 1.3rem;
            line-height: 1.5;
            margin-top: 20px;
        }
        .cancelled {
            grid-area: 1 / 1 / 3 / 3;
        }
        .forms, .rooms {
            flex-direction: column;
            align-items: center;
        }
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
    .plan {
        & > div {
            &:empty {
                outline-color: transparent !important;
            }
            display: flex;
            flex-direction: column;
            gap: 10px;
            outline: solid 3px transparent;
            outline-offset: 5px;
            @media only screen and (max-width: 601px) {
                outline-width: 2px;
                outline-offset: 1px;
            }
            border-radius: 1px;
            transition: all .2s ease;
            transition-delay: .1s;
            .card {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 5px;
                padding: 10px;
                .lesson-time-info {
                    gap: 5px;
                }
            }
            &.loading {
                outline-offset: 10px;
                outline-color: rgba(255, 255, 255, 0.4);
                @media only screen and (max-width: 601px) {
                    outline-offset: 4px;
                }
            }
        }
        &.extra-height {
            min-height: calc(100vh - 20px);
        }
    }
</style>