<script>
    import {customFetch, get_favorites, load_meta} from "../utils.js";
    import Select from "../base_components/Select.svelte";
    import Button from "../base_components/Button.svelte";
    import {notifications} from "../notifications.js";

    import {favorites, title, settings} from "../stores.js";
    import CollapsibleWrapper from "../base_components/CollapsibleWrapper.svelte";
    import Collapsible from "../base_components/Collapsible.svelte";
    import { onMount } from "svelte";

    let cur_favorites = [];
    let loading = true;
    let all_schools = {};
    let authorized_school_ids = [];
    let school_nums = [];
    $: school_nums = [...new Set(cur_favorites.map(obj => obj.school_num).filter(school_num => school_num !== ""))];
    let all_meta = {};
    let duplicated_courses_match = {};
    let plan_types = [
        {"display_name": "Klassenplan", "id": "forms"},
        {"display_name": "Lehrerplan", "id": "teachers"},
        {"display_name": "Raumplan", "id": "rooms"},
        {"display_name": "Freie Räume", "id": "room_overview"}
    ];
    let plan_type_map = {
        "forms": "Klasse",
        "teachers": "Lehrer",
        "rooms": "Raum"
    }
    $: update_meta(school_nums);

    get_schools();
    get_authorized_schools();
    get_favorites()
        .then(data => {
            load_favorites()
        });

    onMount(() => {
        location.hash = "#favorites";
        title.set("Favoriten");
    });

    // duplicate from school manager but hard to simplify
    function get_schools() {
        customFetch("/api/v69.420/schools")
            .then(data => {
                all_schools = Object.fromEntries(data.map(obj => [obj._id, obj]));
            })
            .catch(error => {
                notifications.danger(error.message);
            })
    }
    function get_authorized_schools() {
        customFetch("/auth/authorized_schools")
            .then(data => {
                authorized_school_ids = data;
            })
            .catch(error => {
                console.error("Autorisierte Schulen konnten nicht ermittelt werden.");
            });
    }


    /*
    preferences procedure:
        - from server: list of courses that are not checked
        - list converted to object ([462, 412] -> {462: false, 412: false})
        - all other courses of form later set to true
        - saving: all courses are extracted that have the false value

        - duplicated courses are unified: for each course c1 that already exists as course c0, the pair c1: c0 is put into an object -> later, the check-value of c1 is set to that of c0
    */
    function load_favorites() {
        loading = true;
        // change preferences to dict
        let temp_fav = $favorites;
        console.log(temp_fav);
        temp_fav = temp_fav.map(item => ({ ...item, preferences: (item.preferences || []).reduce((obj, preference) => ({ ...obj, [preference]: false }), {}) }));
        cur_favorites = temp_fav;
        console.log(cur_favorites);
        loading = false;
    }
    function save_favorites() {
        let new_favorites = [];
        for (let favorite = 0; favorite < cur_favorites.length; favorite++) {
            let cur_favorite = {...cur_favorites[favorite]};
            // check if favorite in duplicated_courses_match
            if (duplicated_courses_match.hasOwnProperty(favorite)) {
                for (const cur_key of Object.keys(duplicated_courses_match[favorite])) {
                    cur_favorite.preferences[cur_key] = cur_favorite.preferences[duplicated_courses_match[favorite][cur_key]];
                }
            }
            cur_favorite.preferences = Object.keys(cur_favorite.preferences).filter(key => cur_favorite.preferences[key] === false);
            new_favorites.push(cur_favorite);
        }
        favorites.set(new_favorites);
        // now the post request
        customFetch("/api/v69.420/favorites", {
            method: "POST",
            body: JSON.stringify(new_favorites),
            headers: {
                "Content-Type": "application/json"
            }
        })
            .then(data => {
                notifications.success("Favoriten gespeichert.");
            })
            .catch(error => {
                notifications.danger(error.message);
            })
    }

    // FAVOURITE MANAGEMENT
    function add_favorite() {
        cur_favorites = [...cur_favorites, {"school_num": "", "name": "", "priority": 0, "plan_type": "", "plan_value": "", "preferences": {}}];
    }
    // clear everything except for the school num of a favorite
    function clear_favorite(favorite) {
        cur_favorites[favorite] = {"school_num": cur_favorites[favorite].school_num, "name": cur_favorites[favorite].name, "priority": 0, "plan_type":cur_favorites[favorite].plan_type, "plan_value": "", "preferences": {}}
        cur_favorites = cur_favorites;
    }
    // delete a favorite
    function delete_favorite(favorite) {
        let new_array = cur_favorites;
        new_array.splice(favorite, 1);
        cur_favorites = new_array;
    }

    // load all metadata for all schools needed
    function update_meta(school_nums) {
        for (let i = 0; i < school_nums.length; i++) {
            if (all_meta.hasOwnProperty(school_nums[i])) {
                continue;
            }
            load_meta(school_nums[i])
                .then(meta => {
                    all_meta[school_nums[i]] = meta[0];
                })
        }
    }
    // getting available teachers/rooms/forms
    function get_values(school_num, plan_type, stored_meta) {
        if (!stored_meta.hasOwnProperty(school_num)) {
            return []
        }
        let meta = stored_meta[school_num];
        let return_lst = [];
        if (plan_type === "teachers") {
            for (const teacher of Object.keys(meta.teachers)) {
                return_lst.push({"id": teacher, "display_name": teacher})
            }
            return return_lst
        } else if (plan_type === "rooms") {
            for (const room of Object.keys(meta.rooms)) {
                return_lst.push({"id": room, "display_name": room})
            }
            return return_lst
        } else if (plan_type === "forms") {
            for (const [form_group, forms] of Object.entries(meta.forms.grouped_forms)) {
                let converted_forms = [];
                for(let form of forms) {
                    converted_forms.push({"id": form, "display_name": form});
                }
                return_lst.push([form_group, converted_forms]);
            }
            return return_lst
        }
        return [];
    }
    // get subjects for one form
    function get_subjects(favorite, stored_meta) {
        let school_num = cur_favorites[favorite].school_num;
        let form = cur_favorites[favorite].plan_value;
        if (!stored_meta.hasOwnProperty(school_num)) {
            return []
        }
        if (!stored_meta[school_num].forms.forms.hasOwnProperty(form)) {
            return []
        }
        duplicated_courses_match[favorite] = {};
        for (const class_group of Object.keys(stored_meta[school_num].forms.forms[form].class_groups)) {
            if (cur_favorites[favorite].preferences[class_group] === undefined) {
                cur_favorites[favorite].preferences[class_group] = true;
            }
        }

        return sort_courses_by_subject(favorite, stored_meta[school_num].forms.forms[form].class_groups)
        //return Object.entries(stored_meta[school_num].forms.forms[form].class_groups);
    }

    function sort_courses_by_subject(favorite, obj) {
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
                    duplicated_courses_match[favorite][class_number] = obj.class_number;
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

    function update_authorized_schools() {
        authorized_schools = [];
        for(const school_id of authorized_school_ids) {
            if(all_schools.hasOwnProperty(school_id)) {
                authorized_schools.push({
                    "display_name": all_schools[school_id].display_name,
                    "id": school_id
                });
            }
        }
    }

    let authorized_schools = [];
    $: authorized_school_ids, all_schools, update_authorized_schools();
</script>

<h1 class="responsive-heading">Favoriten</h1>
<CollapsibleWrapper class="extra-accordion-padding" let:closeOtherPanels>
    {#each cur_favorites as _, favorite}
        <Collapsible on:panel-open={closeOtherPanels} let:toggle>
            <button slot="handle" on:click={toggle} class="toggle-button" class:first={favorite == 0} class:load_first_favorite={$settings.load_first_favorite}>{cur_favorites[favorite].name ? cur_favorites[favorite].name : "Unbenannter Favorit"}</button>
            <div class="wrapper-content">
                <label for="favorite_name">Name des Favoriten</label>
                <input name="favorite_name" type="text" maxlength="40" class="textfield" bind:value={cur_favorites[favorite].name}>
                <Select data={authorized_schools} bind:selected_id={cur_favorites[favorite].school_num} onchange={() => clear_favorite(favorite)}>Schule auswählen</Select>

                <Select data={plan_types} bind:selected_id={cur_favorites[favorite].plan_type} onchange={() => {cur_favorites[favorite].plan_value = ""; cur_favorites[favorite].preferences = {}}}>Planart auswählen</Select>
                {#if cur_favorites[favorite].plan_type}
                    {#if cur_favorites[favorite].plan_type === "forms"}
                        <Select data={get_values(cur_favorites[favorite].school_num, cur_favorites[favorite].plan_type, all_meta)} grouped={true} bind:selected_id={cur_favorites[favorite].plan_value} data_name="{cur_favorites[favorite].plan_type}">{plan_type_map[cur_favorites[favorite].plan_type]} auswählen</Select>
                        <!--choosable courses-->
                        <div class="course_chooser">
                            {#each Object.entries(
                                get_subjects(favorite, all_meta)
                            ).sort(([subj1, _], [subj2, __]) => subj1.localeCompare(subj2)).sort(([_, courses1], [__, courses2]) => courses2.length - courses1.length) as [subject, courses]}
                                <div class="horizontal-align margin-bottom">
                                    <h1 class="responsive-heading subject-heading">{subject}</h1>
                                    {#if courses.length > 2}
                                        <Button on:click={() => {
                                            for (const course of courses) {
                                                cur_favorites[favorite].preferences[course.class_number] = true;
                                            }
                                        }}
                                        small={true}>Alle Auswählen</Button>
                                        <Button on:click={() => {
                                            for (const course of courses) {
                                                cur_favorites[favorite].preferences[course.class_number] = false;
                                            }
                                        }}
                                        small={true}>Keinen Auswählen</Button>
                                    {/if}
                                </div>
                                <ul class="course-list">
                                    {#each courses as course}
                                        <li>
                                            <input
                                                type="checkbox"
                                                bind:checked={cur_favorites[favorite].preferences[course.class_number]}
                                            />
                                            <!-- {course.class_number} -->
                                            {#if course.group != null}
                                                {course.group}
                                            {:else}
                                                {course.subject}
                                            {/if}
                                            | {course.teacher}
                                        </li>
                                    {/each}
                                </ul>
                            {:else}
                                Wähle eine Klasse um die Kurse für sie zu wählen
                            {/each}
                        </div>
                    {:else if cur_favorites[favorite].plan_type !== "room_overview"}
                        <Select data={get_values(cur_favorites[favorite].school_num, cur_favorites[favorite].plan_type, all_meta)} grouped={false} bind:selected_id={cur_favorites[favorite].plan_value} data_name="{cur_favorites[favorite].plan_type}">{plan_type_map[cur_favorites[favorite].plan_type]} auswählen</Select>
                    {/if}
                {/if}
                <Button on:click={() => {delete_favorite(favorite);}} background="var(--cancelled-color)">Favorit löschen</Button>
            </div>
        </Collapsible>
    {:else}
        {#if loading}
            <Collapsible>
                <button slot="handle" class="toggle-button first"><span class="material-symbols-outlined rotating">sync</span></button>
            </Collapsible>
        {/if}
    {/each}
    <Collapsible on:panel-open={closeOtherPanels}>
        <button slot="handle" on:click={add_favorite} class="toggle-button last" style="font-weight: 600;"><span class="material-symbols-outlined">add</span> Favorit hinzufügen</button>
    </Collapsible>
</CollapsibleWrapper>
<Button on:click={save_favorites} background="var(--accent-color)">Speichern</Button>

<style lang="scss">
    :global(.extra-accordion-padding) {
        margin: 20px 0px;
    }

    .toggle-button {
        font-size: var(--font-size-base);
        width: 100%;
        border: none;
        padding: .7em;
        background-color: rgba(255, 255, 255, 0.05);
        color: var(--text-color);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        transition: background-color .2s ease;

        &.first {
            border-top: unset;

            &.load_first_favorite {
                outline: 2px solid var(--accent-color);
                outline-offset: -2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                @media only screen and (min-width: 1501px) {
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
            }
        }

        &.last {
            border-bottom: unset;
        }

        &:hover, &:focus-visible {
            background-color: rgba(255, 255, 255, 0.03);
        }
    }

    .wrapper-content {
        padding: 20px 0px;
        margin: 0px 5px;
        display: flex;
        flex-direction: column;
        row-gap: 10px;
    }

    .toggle-button .material-symbols-outlined {
        vertical-align: middle;
        font-size: 1.5em;
    }

    label {
        margin-bottom: -2px;
        font-size: var(--font-size-base);
    }

    .textfield {
        width: auto;
        padding: 12px 20px;
        box-sizing: border-box;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.1);
        color: var(--text-color);
        border-radius: 5px;
        font-size: var(--font-size-sm);
    }

    .course_chooser {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 5px;
        padding: 10px;
        border: 2px solid rgba(255, 255, 255, 0.1);
        font-size: var(--font-size-base);
    }

    .rotating {
        animation: rotating .75s linear infinite;
        transform-origin: 50% 48%;
    }

    @keyframes rotating {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }

    .horizontal-align {
        display: flex;
        flex-direction: row;
        gap: 10px;
        align-items: center;
        justify-content: flex-start;
    }

    .margin-bottom {
        margin-bottom: 5px;
    }

    .subject-heading {
        margin-bottom: 0px !important;
    }

    .course-list {
        margin-bottom: 15px;
    }
</style>