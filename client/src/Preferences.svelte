<script>

    import {notifications} from "./notifications.js";
    import {preferences} from './stores.js';
    import {customFetch} from "./utils.js";

    export let api_base;
    export let grouped_forms;
    export let course_lists;
    let selected_form = null;
    let form_groups;
    $: form_groups = selected_form != null ? sortCourses(course_lists[selected_form]["class_groups"]): [];

    let allItems = [];
    let selection = {};
    let current_form_preferences = [];


    function sortCourses(obj) {
        const sortedArray = Object.entries(obj).sort((a, b) => a[1]["group"] - b[1]["group"]);
        const sortedObject = {};
        sortedArray.forEach(([key, value]) => {
            sortedObject[key] = value;
        });
        return sortedObject;
    }

    function getFalse(obj) {
        const falseItems = [];
        for (const key in obj) {
            if (obj.hasOwnProperty(key) && obj[key] === false) {
                falseItems.push(key);
            }
        }
        return falseItems;
    }

    function updateCourses() {
        if (selected_form === null) {
             return
        }
        allItems = Object.keys(course_lists[selected_form]["class_groups"]);
        current_form_preferences = $preferences[selected_form] || [];
        selection = {};
        for (const item of allItems) {
            selection[item] = !current_form_preferences.includes(item);
        }
    }


    function getPreferences() {
        customFetch(`${api_base}/preferences`)
            .then(data => {
                preferences.set(data);
            })
            .catch(error => {
                notifications.danger(error)
            })
    }

    function setPreferences() {
        customFetch(`${api_base}/preferences?` + new URLSearchParams(
            {
                "form": selected_form
            }
        ), {
            method: "POST",
            body: JSON.stringify(getFalse(selection))
        })
            .then(data => {
                notifications.info("Kurse gespeichert!", 2000);
            })
            .catch(error => {
                notifications.danger(error);
            })
    }

    getPreferences();
    updateCourses();

    function select_all() {
        for (const key in selection) {
            if (selection.hasOwnProperty(key)) {
                selection[key] = true;
            }
        }
    }
    function select_none() {
        for (const key in selection) {
            if (selection.hasOwnProperty(key)) {
                selection[key] = false;
            }
        }
    }
    function reverse_selection() {
        for (const key in selection) {
            if (selection.hasOwnProperty(key)) {
                selection[key] = !selection[key];
            }
        }
    }


</script>


{#if selected_form != null}
    <button on:click={select_all}>Alle auswählen</button>
    <button on:click={select_none}>Nichts auswählen</button>
    <button on:click={reverse_selection}>Auswahl invertieren</button>
    <br>
{/if}
Klasse wählen:
<select name="forms" bind:value={selected_form} on:change={updateCourses}>
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
                <input
                    type="checkbox"
                    bind:checked={selection[course_id]}
                />
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