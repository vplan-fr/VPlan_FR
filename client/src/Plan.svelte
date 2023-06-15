<script>
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
    
    function load_lessons(date, plan_type, entity) {
        loading = true;
        title = `${plan_type}-plan for ${plan_type} ${entity}`
        fetch(`${api_base}/plan?date=${date}`)
            .then(response => response.json())
            .then(data => {
                loading = false;
                try {
                    lessons = data["plans"][plan_type][entity] || [];
                    info = data["info"];
                } catch {
                    lessons = []
                }
            })
            .catch(error => {
                console.error(error);
        });
    }

    function periods_to_block_label(periods) {
        periods.sort(function (a, b) {  return a - b;  });

        const rests = {
            0: " (2/2)",
            1: " (1/2)",
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
        {#if lessons.length == 0 && !loading}
            No Lessons
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
                    <div class="subject max-width-center wide-area" class:changed={lesson.subject_changed}>
                        {lesson.current_subject}
                    </div>
                    <div class="teachers vert-align max-width-center info-element small-area" class:changed={lesson.teacher_changed} class:teacher_absent={lesson.current_teacher === null}>
                        <button on:click={() => {
                            plan_type = "teachers";
                            plan_value = lesson.current_teacher === null ? lesson.class_teacher : lesson.current_teacher;
                        }}>{lesson.current_teacher === null ? lesson.class_teacher : lesson.current_teacher}</button>
                    </div>
                    <div class="rooms vert-align max-width-center info-element small-area second_of_type" class:changed={lesson.room_changed}>
                        {#each lesson.rooms as room}
                            <button on:click={() => {
                                plan_type = "rooms";
                                plan_value = room;
                            }}>{room}</button>
                        {:else}
                            X
                        {/each}
                    </div>
                    {:else}
                    <div class="max-width-center info-element cancelled vert-align changed">X</div>
                    {/if}
                    {#if plan_type !== "forms"}
                    <div class="forms max-width-center wide-area second_of_type info-element">
                        {#each lesson.forms as form}
                            <button on:click={() => {
                                plan_type = "forms";
                                plan_value = form;
                            }}>{form}</button>
                        {/each}
                    </div>
                    {/if}
                </div>
            </div>
            {#if lesson.info}
                <div class="info-element lesson-info">{lesson.info}</div>
            {/if}
        </div>
        <div class="card mobile-view">
            <div class="horizontal-align">
                <div class="vert-align max-width-center lesson-time-info">
                    <span class="lesson-period">{periods_to_block_label(lesson.periods)}</span>
                    <span class="lesson-time">{lesson.begin}</span>
                </div>
                {#if lesson.current_subject !== "---"}
                <div class="subject max-width-center" class:changed={lesson.subject_changed}>
                    {lesson.current_subject}
                </div>
                <div class="teachers vert-align max-width-center info-element" class:changed={lesson.teacher_changed} class:teacher_absent={lesson.current_teacher === null}>
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
                        X
                    {/each}
                </div>
                {:else}
                <div class="max-width-center info-element cancelled vert-align changed">X</div>
                {/if}
                {#if plan_type !== "forms"}
                <div class="forms max-width-center info-element vert-align">
                    {#each lesson.forms as form}
                        <button on:click={() => {
                            plan_type = "forms";
                            plan_value = form;
                        }}>{form}</button>
                    {/each}
                </div>
                {/if}
            </div>
            {#if lesson.info}
                <div class="info-element lesson-info">{lesson.info}</div>
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
    .no-linebreak {
        white-space: nowrap;
    }
    .grid-align-wrapper {
        width: 100%;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        grid-template-rows: min-content 1fr;
        &.large_grid {
            grid-template-rows: min-content 1fr min-content;
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
        margin-top: 16px;
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
    }

    .info-element {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 5px;
        padding: 5px 0px;
        min-height: 21px;
        overflow: hidden;
        
        button {
            transition: background-color .2s ease;
            width: 100%;
            padding: 5px;
            margin: -5px;
            line-height: 1.313rem;

            &:hover, &:focus-visible {
                background: rgba(0, 0, 0, 0.2) !important;
            }
        }
        
        &.changed {
            background: var(--accent-color);

            &:not(.teacher_absent) {
                button:hover, button:focus-visible {
                    background: rgba(0, 0, 0, 0.3) !important;
                }
            }
        }
        &.teacher_absent {
            background: rgba(255, 255, 255, 0.08);
            outline: 3px solid var(--accent-color);
            outline-offset: -3px;
        }
    }

    .rooms, .forms {
        gap: 10px;
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
        .subject, .info-element, .info-element button {
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
            padding: 1rem 0;
            button {
                padding: 2rem;
                margin: -2rem;
            }
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
        .subject, .info-element, .info-element button {
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
            gap: 2rem;
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
            }
        }
        &.extra-height {
            min-height: calc(100vh - 20px);
        }
    }
</style>