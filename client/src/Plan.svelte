<script>
    export let api_base;
    export let date;
    export let plan_type;
    export let plan_value;
    export let meta;
    let lessons = [];
    let title = "";
    
    function load_lessons(date, plan_type, entity) {
        title = `${plan_type}-plan for ${plan_type} ${entity}`
        fetch(`${api_base}/plan?date=${date}`)
            .then(response => response.json())
            .then(data => {
                lessons = data["plans"][plan_type][entity] || [];
                console.log(lessons);
            })
            .catch(error => {
                console.error(error);
        });
    }

    $: load_lessons(date, plan_type, plan_value);
</script>

{#if lessons.length == 0}
No lessons
{/if}
{#each lessons as lesson}
    <div class="card lesson-head">{lesson.begin}-{lesson.end} (#{lesson.period})</div>
    <div class="card clickable">
        <button on:click={() => {
            plan_type = "form_plan";
            plan_value = lesson.form;
        }}>{lesson.form}</button>
    </div>
    <div class="card">{lesson.current_subject}</div>
    <div class="card clickable">
        <button on:click={() => {
            plan_type = "teacher_plan";
            plan_value = lesson.current_teacher;
        }}>{lesson.current_teacher}</button>
    </div>
    <div class="card clickable">
        <button on:click={() => {
            plan_type = "room_plan";
            plan_value = lesson.room;
        }}>{lesson.room}</button>
    </div>
    {#if lesson.info}
        <div class="card">{lesson.info}</div>
    {/if}
    <br>
{/each}

<style>
</style>