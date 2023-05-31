<script>
    export let api_base;
    export let date;
    export let plan_type;
    export let plan_value;
    let lessons = [];
    let title = "";
    
    function load_lessons(date, plan_type, entity) {
        title = `${plan_type}-plan for ${plan_type} ${entity}`
        fetch(`${api_base}/plan?date=${date}`)
            .then(response => response.json())
            .then(data => {
                try {
                    lessons = data["plans"][plan_type][entity] || [];
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

<div class="plan">
    {#if lessons.length == 0}
    No lessons
    {/if}
    {#each lessons as lesson}
    <div class="card">
        <div>{lesson.begin}-{lesson.end} (#{lesson.period})</div>
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
    {/each}
</div>

<style lang="scss">
    .plan {
        display: flex;
        flex-direction: column;
        gap: 10px;
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
        }
    }
</style>