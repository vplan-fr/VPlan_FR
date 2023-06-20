<script>
    import Lesson from './Lesson.svelte';

    export let api_base;
    export let date;
    export let plan_type;
    export let plan_value;
    export let show_title = true;
    export let extra_height = true;
    export let week_letter;
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
            })
            .catch(error => {
                console.error(error);
        });
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
            <Lesson lesson={lesson} bind:plan_type bind:plan_value display_time={false} />
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
</style>