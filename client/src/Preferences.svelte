<script>

    export let api_base;
    export let grouped_forms;
    export let course_lists;
    let current_preferences;
    let selected_form;
    $: console.log(course_lists);
    $: forms_list = Object.keys(course_lists);

    let selectedItems = [];


    function toggleSelection(course_id) {
        console.log(course_id);
        if (!selectedItems.includes(course_id)) {
            selectedItems.push(course_id)
        } else {
            selectedItems.splice(selectedItems.indexOf(course_id), 1)
        }
        console.log(selectedItems);
    }

    function updateCourses() {
        selectedItems = Object.keys(course_lists[selected_form]["class_groups"]);
    }

    function getPreferences() {
        fetch(`${api_base}/preferences`)
            .then(response => response.json())
            .then(data => {
                current_preferences = data;
                console.log(current_preferences)
            })
    }

    getPreferences()

</script>


Klasse wählen: <select name="forms" bind:value={selected_form} on:change={updateCourses}>
    {#each Object.entries(grouped_forms) as [form_group, forms]}
        <optgroup label={form_group}>
            {#each forms as form}
                <option value="{form}">{form}</option>
            {/each}
        </optgroup>
    {/each}
</select>
<div>Selected form: {selected_form}</div>
{#if selected_form != null}
    Verfügbare Kurse:
    <ul>
        {#each Object.keys(course_lists[selected_form]["class_groups"]) as course_id}
            <li>
                <input
                    type="checkbox"
                    on:change={() => toggleSelection(course_id)}
                  />
                {course_id}
                {course_lists[selected_form]["class_groups"][course_id]["teacher"]} |
                {course_lists[selected_form]["class_groups"][course_id]["subject"]}
                ({course_lists[selected_form]["class_groups"][course_id]["group"]})
            </li>
        {/each}
    </ul>
{/if}

<style lang="scss">

</style>