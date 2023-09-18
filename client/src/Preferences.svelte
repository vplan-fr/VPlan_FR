<script>
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

    // [("Überschrift", [{id: "", name: "", icon: ""}, {}]), (...)]

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
                notifications.success("Kurse gespeichert!", 2000);
            })
            .catch(error => {
                notifications.danger(error.message);
            })
    }

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

    onMount(() => {
        if(!school_num) {
            navigate_page('school_manager');
            return;
        }
        updateCourses();
        location.hash = "#preferences";
        title.set("Unterricht wählen");
    });

    $: create_select_arr(grouped_forms)
    $: selected_form, updateCourses();
</script>

<h1 class="responsive-heading">Unterrichtswahl</h1>
<Select data={select_arr} grouped={true} bind:selected_id={selected_form}>Klasse auswählen</Select>
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
                    <button on:click={() => {select_all_part(courses)}} class="button">Alle auswählen</button>
                    <button on:click={() => {select_none_part(courses)}} class="button">Keinen auswählen</button>
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
    <button on:click={setPreferences} class="button" style="background: var(--accent-color);">Speichern</button>
{/if}

<style lang="scss">
    .button {
        overflow: hidden;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: none;
        background-color: rgba(255, 255, 255, 0.2);
        color: var(--text-color);
        border-radius: 5px;
        padding: .5em;
        margin: 3px;
        font-size: 1rem;
        position: relative;

        &.btn-small {
            font-size: var(--font-size-sm);
        }

        .material-symbols-outlined {
            font-size: 1.3em;
            float: right;
            margin-left: .2em;
        }
    }
</style>