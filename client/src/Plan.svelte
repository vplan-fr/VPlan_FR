<script>
    import Lesson from './Lesson.svelte';

    export let api_base;
    export let date;
    export let plan_type;
    export let plan_value;
    export let show_title = true;
    export let extra_height = true;
    export let week_letter = "";
    export let external_times = true;

    let lessons = [];
    let info;
    let title = "";
    let loading = true;
    let plan_type_map = {
        "forms": "Klasse",
        "rooms": "Raum",
        "teachers": "Lehrer"
    };
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
                    week_letter = info.week;
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

    function arraysEqual(a, b) {
        if (a === b) return true;
        if (a == null || b == null) return false;
        if (a.length !== b.length) return false;

        a.sort(function (a, b) {  return a - b;  });
        b.sort(function (a, b) {  return a - b;  });

        for (var i = 0; i < a.length; ++i) {
            if (a[i] !== b[i]) return false;
        }
        return true;
    }

    function sameBlock(a, b) {
        return a.includes(b[0]) || a.includes(b[1])
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
        <div class="lessons-wrapper">
            {#if external_times}
                <div class="deco-bar"></div>
            {/if}
            {#each lessons as lesson, i}
                {#if external_times}    
                    {#if !lessons[i-1] || (!arraysEqual(lesson.periods, lessons[i-1].periods))}
                        <span class="lesson-time" class:gap={lessons[i-1] && !sameBlock(lesson.periods, lessons[i-1].periods)}>{periods_to_block_label(lesson.periods)}: {lesson.begin} - {lesson.end}</span>
                    {/if}
                {/if}
                <Lesson lesson={lesson} bind:plan_type bind:plan_value display_time={!external_times} />
            {/each}
        </div>
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
    .plan {
        & > div, & .lessons-wrapper {
            &:empty {
                outline-color: transparent !important;
            }
            position: relative;
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
        line-height: 1.5;
    }

    .additional-info {
        margin-top: 20px;
        font-size: clamp(0.938rem, 3vmin, 1.875rem);
        line-height: 1.5;
    }

    .no-linebreak {
        white-space: nowrap;
    }

    .lessons-wrapper {
        --bar-width: 15px;
        .lesson-time {
            position: relative;
            margin-left: -10px;
            background: rgba(255, 255, 255, 0.1);
            width: max-content;
            border-radius: 0px 8px 8px 0px;
        
            font-size: 1.875rem;
            padding: 1rem;
            line-height: 1;
            
            @media only screen and (max-width: 601px) {
                margin-left: 0px;
                border-radius: 5px;
        
                font-size: 0.875rem;
                padding: 5px;
                line-height: normal;
            }

            &.gap::before {
                content: "";
                position: absolute;
                top: calc(-1 * var(--bar-width));
                left: calc(-1 * var(--bar-width));

                width: var(--bar-width);
                aspect-ratio: 1;

                background: radial-gradient(circle at 50% -15% , transparent calc(.5 * var(--bar-width)), var(--background-color) calc(.5 * var(--bar-width) + .5px));
            }
            
            &.gap::after {
                content: "";
                position: absolute;
                top: 0px;
                left: calc(-1 * var(--bar-width));

                width: var(--bar-width);
                aspect-ratio: 1;

                background: radial-gradient(circle at 100% 100% , transparent var(--bar-width), var(--background-color) calc(var(--bar-width) + .5px));
            }
        }

        .deco-bar {
            position: absolute;
            top: 0;
            left: calc(-1 * var(--bar-width) - 10px);
    
            background: rgba(255, 255, 255, 0.1);
            height: 100%;
            width: var(--bar-width);
    
            border-radius: var(--bar-width) 0px var(--bar-width) var(--bar-width);
    
            @media only screen and (max-width: 601px) {
                display: none;
            }
        }
    }
</style>