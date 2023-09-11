<script>

    import {notifications} from "./notifications.js";
    import {preferences} from "./stores.js";

    export let api_base;
    export let grouped_forms;
    export let course_lists;
    let selected_form;
    let form_groups;
    $: form_groups = selected_form != null ? sortCourses(course_lists[selected_form]["class_groups"]): [];

    let allItems = [];
    let selection = {};
    let selectedItems = [];
    let current_form_preferences = [];

    $: console.log(form_groups);

    function sortCourses(obj) {
        const sortedArray = Object.entries(obj).sort((a, b) => a[1]["group"] - b[1]["group"]);
        const sortedObject = {};
        sortedArray.forEach(([key, value]) => {
            sortedObject[key] = value;
        });
        return sortedObject;
    }
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
        allItems = Object.keys(course_lists[selected_form]["class_groups"]);
        selection = {};

        current_form_preferences = $preferences[selected_form] || [];
        selectedItems = allItems.filter(item => current_form_preferences.indexOf(item) !== -1);
    }


    function getPreferences() {
        fetch(`${api_base}/preferences`)
            .then(response => response.json())
            .then(data => {
                preferences.set(data);
            })
    }

    function setPreferences() {
        fetch(`${api_base}/preferences?` + new URLSearchParams(
            {
                "form": selected_form
            }
        ), {
            method: "POST",
            body: JSON.stringify(selectedItems)
        })
            .then(response => response.json())
            .then(data => {
                if (data["success"]) {
                    notifications.info("Kurse gespeichert!", 2000);
                }
            })
    }

    getPreferences()
    function isChecked(id) {
        return selectedItems.includes(id)
    }

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
    <button on:click={setPreferences}>Speichern</button>
    Verfügbare Kurse:
    <ul>
        {#each Object.keys(form_groups) as course_id}
            <li>
                {#if current_form_preferences.includes(course_id)}
                    <input
                        type="checkbox"
                        on:change={() => toggleSelection(course_id)}
                      />
                {:else}
                    <input
                        type="checkbox"
                        on:change={() => toggleSelection(course_id)}
                        checked
                    />
                {/if}
                {course_id}
                {form_groups[course_id]["teacher"]} |
                {form_groups[course_id]["subject"]}
                ({form_groups[course_id]["group"]})
            </li>
        {/each}
    </ul>
{/if}

<style lang="scss">

</style>