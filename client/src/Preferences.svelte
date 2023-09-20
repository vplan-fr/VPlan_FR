<script>
    import Button from "./Components/Button.svelte";
    import Select from "./Components/Select.svelte";
    import {notifications} from "./notifications.js";
    import {preferences, title} from './stores.js';
    import {customFetch, navigate_page} from "./utils.js";
    import { onMount } from "svelte";

    export let api_base;
    export let grouped_forms;
    export let course_lists;
    export let school_num;
    let selected_form = null;
    let class_groups_by_subject = [];
    $: class_groups_by_subject = selected_form != null ? sort_courses_by_subject(course_lists[selected_form]["class_groups"]) : [];

    let allItems = [];
    let selection = {};
    let current_form_preferences = [];
    let select_arr = [];
    // used to match every course that exists duplicated to one id -> see set_preferences
    let duplicated_courses_match = {};

    function create_select_arr(grouped_forms) {
        select_arr = []
        for (const [form_group, forms] of Object.entries(grouped_forms)) {
            let converted_forms = [];
            for(let form of forms) {
                converted_forms.push({"id": form, "name": form});
            }
            select_arr.push([form_group, converted_forms]);
        }
    }

    function sort_courses_by_subject(obj) {
        const courses_by_subject = {};

        Object.entries(obj).forEach(([class_number, class_data]) => {
            const subject = class_data.subject;
            if (courses_by_subject[subject] === undefined) {
                courses_by_subject[subject] = [];
            }
            class_data.class_number = class_number;
            // this is for the duplicated forms
            let object_exists = false;
            for (const obj of courses_by_subject[subject]) {
                if (
                    Object.keys(class_data)
                        .filter(key => key !== "class_number")
                        .every(key => obj[key] === class_data[key])
                ) {
                    duplicated_courses_match[class_number] = obj.class_number;
                    object_exists = true;
                    break;
                }
            }
            if (!object_exists) {
                courses_by_subject[subject].push(class_data);
            }
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

    function setPreferences() {
        for (const cur_key of Object.keys(duplicated_courses_match)) {
            selection[cur_key] = selection[duplicated_courses_match[cur_key]]
        }
        customFetch(`${api_base}/preferences?` + new URLSearchParams(
            {
                "form": selected_form
            }
        ), {
            method: "POST",
            body: JSON.stringify(getFalse(selection))
        })
            .then(data => {
                notifications.success("Kurse gespeichert!", 2000);
            })
            .catch(error => {
                notifications.danger(error.message);
            })
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

    onMount(() => {
        if(!school_num) {
            navigate_page('school_manager');
            return;
        }
        updateCourses();
        location.hash = "#preferences";
        title.set("Unterricht wählen");
        // console.log("Mounted Preferences.svelte");
    });

    $: create_select_arr(grouped_forms)
    $: selected_form, updateCourses();
</script>

<h1 class="responsive-heading">Unterrichtswahl</h1>
<Select data={select_arr} grouped={true} bind:selected_id={selected_form} data_name="Klassen">Klasse auswählen</Select>
{#if selected_form != null}
    <ul class="responsive-text">
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
                    {#if courses.length > 2}
                    <Button class="inline-flex" on:click={() => {select_all_part(courses)}}>Alle Auswählen</Button>
                    <Button class="inline-flex" on:click={() => {select_none_part(courses)}}>Keinen Auswählen</Button>
                    {/if}
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
{#if selected_form != null}
    <Button on:click={setPreferences} background="var(--accent-color)">Speichern</Button>
{/if}

<style lang="scss">
    :global(.inline-flex) {
        display: inline-flex !important;
    }
</style>