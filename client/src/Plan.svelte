<script>
    export let api_base;
    export let date;
    export let plan_type;
    export let plan_value;
    let lessons = [];
    let info;
    let title = "";
    
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
                console.log(lessons);
            })
            .catch(error => {
                console.error(error);
        });
    }

    $: load_lessons(date, plan_type, plan_value);
    $: console.log(info);
</script>

<div class="plan">
    {#if lessons.length == 0}
    No lessons
    {/if}
    {#if info}
        <div>
            Stand: {info.timestamp}
        </div>
    {/if}
    {#each lessons as lesson}
    <div class="card desktop-view">
        <div>{lesson.begin}-{lesson.end} (#{lesson.periods[1]/2})</div>
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
                <span class="lesson-period">{lesson.periods[1]/2}</span>
                <span class="lesson-time">{lesson.begin}</span>
            </div>
            {#if lesson.current_subject !== "---"}
            <div class="subject max-width-center" class:changed={lesson.subject_changed}>
                {lesson.current_subject}
            </div>
            <div class="teachers vert-align max-width-center info-element" class:changed={lesson.teacher_changed} class:teacher_absent={lesson.current_teacher === null}>
                <button on:click={() => {
                    plan_type = "teachers";
                    plan_value = lesson.current_teacher;
                }}>{lesson.current_teacher === null ? lesson.class_teacher : lesson.current_teacher}</button>
            </div>
            <div class="rooms vert-align max-width-center info-element" class:changed={lesson.room_changed}>
                {#each lesson.rooms as room}
                    <button on:click={() => {
                        plan_type = "rooms";
                        plan_value = room;
                    }}>{room}</button>
                {/each}
            </div>
            {:else}
            <div class="max-width-center info-element mobile-cancelled vert-align changed">X</div>
            {/if}
            {#if plan_type !== "forms"}
            <div class="forms max-width-center info-element">
                <button on:click={() => {
                    plan_type = "forms";
                    plan_value = lesson.form;
                }}>{lesson.form}</button>
            </div>
            {/if}
        </div>
        {#if lesson.info}
            <div class="info-element lesson-info">{lesson.info}</div>
        {/if}
    </div>
    {/each}
    {#if info}
        <div>
            {#each info.additional_info as cur_info}
                {cur_info}<br>
            {/each}
        </div>
    {/if}
</div>

<style lang="scss">
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

        button {
            padding: 0;
            line-height: 21px;
        }
        
        &.changed {
            background: var(--accent-color);
        }
        &.teacher_absent {
            background: rgba(255, 255, 255, 0.08);
            outline: 3px solid var(--accent-color);
        }
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
    }
</style>