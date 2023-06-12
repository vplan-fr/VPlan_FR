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
    let plan_type_map = {
        "forms": "Klasse",
        "rooms": "Raum",
        "teachers": "Lehrer"
    }
    
    function load_lessons(date, plan_type, entity) {
        title = `${plan_type}-plan for ${plan_type} ${entity}`
        fetch(`${api_base}/plan?date=${date}`)
            .then(response => response.json())
            .then(data => {
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
        periods.sort();

        const rests = {
            0: " - 2",
            1: " - 1",
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
    {#if show_title && info}
        <div class="responsive-heading">
            Plan für {plan_type_map[plan_type]} <span class="custom-badge">{plan_value}</span> am <span class="custom-badge">{date}</span> ({info.week}-Woche)
        </div>
    {/if}
    {#if lessons.length == 0}
    No lessons
    {/if}
    {#each lessons as lesson}
    <div class="card desktop-view">
        <div>{lesson.begin}-{lesson.end} ({periods_to_block_label(lesson.periods)})</div>
        <div>
            <button on:click={() => {
                plan_type = "forms";
                plan_value = lesson.form;
            }}>{lesson.form}</button>
        </div>
        <div>{lesson.current_subject}</div>
        <div>
            <button on:click={() => {
                plan_type = "teachers";
                plan_value = lesson.current_teacher;
            }}>{lesson.current_teacher}</button>
        </div>
        <div>
            {#each lesson.rooms as room}
                <button on:click={() => {
                    plan_type = "rooms";
                    plan_value = room;
                }}>{room}</button>
            {/each}
        </div>
        {#if lesson.info}
            <div>{lesson.info}</div>
        {/if}
        <br>
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
            <div class="max-width-center info-element mobile-cancelled vert-align changed">X</div>
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

<style lang="scss">
    .responsive-heading {
        font-size: clamp(17px, 4vw, 2.28rem);
        line-height: clamp(22.5px, 4.5vmax, 45px);
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
        font-size: clamp(14px, 2.8vmin, 28px);
    }

    .additional-info {
        margin-top: 20px;
        font-size: clamp(15px, 3vmin, 30px);
        line-height: 1.5;
    }

    .mobile-cancelled {
        width: 400% !important;
    }
    .forms {
        font-size: 14px;
    }
    .lesson-info {
        margin-top: 12px;
        padding: 8px !important;
        font-size: 14px;
        font-weight: 300;
        line-height: 21px;
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
            line-height: 21px;

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
        }
    }

    .rooms, .forms {
        gap: 10px;
    }

    .mobile-view {
        display: none;
        @media only screen and (max-width: 600px) {
            display: block;
        }
        .lesson-period {
            font-size: 14px;
            font-weight: 400;
        }
        .lesson-time {
            font-size: 12px;
            font-weight: 400;
        }
        .subject, .teachers button, .rooms button, .forms button {
            color: var(--text-color);
            font-size: 14px;
            font-weight: 400;
            border: none;
            background: none;
        }
        .teachers button {
            font-weight: 600;
        }
    }
    .desktop-view {
        display: none;
        @media only screen and (min-width: 601px) {
            display: block;
        }
    }
    .horizontal-align {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        gap: 8vw;
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
        display: flex;
        flex-direction: column;
        gap: 10px;
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
            padding: 10px;
            .lesson-time-info {
                gap: 5px;
            }
        }

        &.extra-height {
            min-height: calc(100vh - 20px);
        }
    }
</style>