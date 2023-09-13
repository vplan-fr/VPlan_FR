<script>

    import {notifications} from "./notifications.js";
    import {preferences} from './stores.js';
    import {customFetch} from "./utils.js";

    export let api_base;
    export let grouped_forms;
    export let course_lists;
    let selected_form = null;
    let class_groups_by_subject = [];
    $: class_groups_by_subject = selected_form != null ? sort_courses_by_subject(course_lists[selected_form]["class_groups"]) : [];

    let allItems = [];
    let selection = {};
    let current_form_preferences = [];


    function sort_courses_by_subject(obj) {
        const courses_by_subject = {};

        Object.entries(obj).forEach(([class_number, class_data]) => {
            const subject = class_data.subject;
            if (courses_by_subject[subject] === undefined) {
                courses_by_subject[subject] = [];
            }
            class_data.class_number = class_number;
            courses_by_subject[subject].push(class_data);
        });

        Object.values(courses_by_subject).map(class_datas => class_datas.sort((data1, data2) => data2.group?.localeCompare(data1.group)));

        return courses_by_subject;
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

    function select_all_part(courses) {
        for (const course in courses) {
            let key = courses[course].class_number;
            if (selection.hasOwnProperty(key)) {
                selection[key] = true;
            }
        }
    }

    function select_none_part(courses) {
        for (const course in courses) {
            let key = courses[course].class_number;
            if (selection.hasOwnProperty(key)) {
                selection[key] = false;
            }
        }
    }

</script>

<h1>Unterrichtswahl</h1>
{#if selected_form != null}
    <button on:click={setPreferences}>Speichern</button>
{/if}

<div>
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
</div>
<div>
    {#if selected_form != null}
        <button on:click={select_all}>Alle auswählen</button>
        <button on:click={select_none}>Nichts auswählen</button>
        <!--<button on:click={reverse_selection}>Auswahl invertieren</button>-->
        <br>
    {/if}
</div>
{#if selected_form != null}
    <ul>

        {#each Object.entries(class_groups_by_subject).sort(([subj1, _], [subj2, __]) => subj1.localeCompare(subj2)).sort(([_, courses1], [__, courses2]) => courses2.length - courses1.length) as [subject, courses]}

            {#if courses.length === 1}
                <li>{subject}:<input
                        type="checkbox"
                        bind:checked={selection[courses[0].class_number]}
                />
                    {courses[0].class_number}
                    {courses[0].teacher} |
                    {courses[0].subject}
                    {#if courses[0].group != null}
                        ({courses[0].group})
                    {/if}
                </li>
            {:else}
                <li>
                    {subject}
                    <button on:click={() => {select_all_part(courses)}}>Alle auswählen</button>
                    <button on:click={() => {select_none_part(courses)}}>Keinen auswählen</button>
                </li>
                <ul>
                    {#each courses as course}
                        <li>
                            <input
                                    type="checkbox"
                                    bind:checked={selection[course.class_number]}
                            />
                            {course.class_number}
                            {course.teacher} |
                            {course.subject}
                            {#if course.group != null}
                                ({course.group})
                            {/if}
                        </li>
                    {/each}
                </ul>
            {/if}
        {/each}
    </ul>
{/if}

<style lang="scss">

</style>