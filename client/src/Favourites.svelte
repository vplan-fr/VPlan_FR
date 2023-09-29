<script>
    import {load_meta} from "./utils.js";
    import Select from "./base_components/Select.svelte";
    import Button from "./base_components/Button.svelte";
    import {onMount} from "svelte";
    import {title} from "./stores.js";

    let favourites = [
        //{"school_num": "10001329", "name": "Arthur", "priority": 0, "plan_type": "forms", "plan_value": "JG12", "preferences": {}}
    ]
    $: console.log(favourites);
    let school_nums = [];
    $: school_nums = [...new Set(favourites.map(obj => obj.school_num))];
    let all_meta = {};
    let duplicated_courses_match = {};
    $: update_meta(school_nums);

    let preferences = {};

    onMount(() => {
        load_favourites();
    });

    function get_pseudo_favourites_from_server() {
        return [
            //{"school_num": "10001329", "name": "Arthur", "priority": 0, "plan_type": "forms", "plan_value": "JG12", "preferences": [607, 609, 616]},
            {"school_num": "10001329", "name": "Leo", "priority": 1, "plan_type": "forms", "plan_value": "6/4", "preferences": ["494", "434"]},
        ]
    }

    /*
    preferences procedure:
        - from server: list of courses that are not checked
        - list converted to object ([462, 412] -> {462: false, 412: false})
        - all other courses of form later set to true
        - saving: all courses are extracted that have the false value

        - duplicated courses are unified: for each course c1 that already exists as course c0, the pair c1: c0 is put into an object -> later, the check-value of c1 is set to that of c0
    */
    function load_favourites() {
        // change preferences to dict
        let temp_fav = get_pseudo_favourites_from_server();
        temp_fav = temp_fav.map(item => ({ ...item, preferences: item.preferences.reduce((obj, preference) => ({ ...obj, [preference]: false }), {}) }));
        console.log(temp_fav)
        favourites = temp_fav;
    }
    function save_favourites() {
        let new_favourites = [];
        for (let favourite = 0; favourite < favourites.length; favourite++) {
            let cur_favourite = {...favourites[favourite]};
            for (const cur_key of Object.keys(duplicated_courses_match[favourite])) {
                cur_favourite.preferences[cur_key] = cur_favourite.preferences[duplicated_courses_match[favourite][cur_key]];
            }
            cur_favourite.preferences = Object.keys(cur_favourite.preferences).filter(key => cur_favourite.preferences[key] === false);
            new_favourites.push(cur_favourite);
        }
        console.log(new_favourites);
    }

    // FAVOURITE MANAGEMENT
    function add_favourite() {
        favourites = [...favourites, {"school_num": "test", "name": "", "priority": 0, "plan_type": "", "plan_value": "", "preferences": {}}];
    }
    // clear everything except for the school num of a favourite
    function clear_favourite(favourite) {
        favourites[favourite] = {"school_num": favourites[favourite].school_num, "name": "", "priority": 0, "plan_type": "", "plan_value": "", "preferences": {}}
    }
    // delete a favourite
    function delete_favourite(favourite) {
        let new_array = favourites;
        new_array.splice(favourite, 1);
        favourites = new_array;
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
    function get_subjects(favourite, stored_meta) {
        let school_num = favourites[favourite].school_num;
        let form = favourites[favourite].plan_value;
        if (!stored_meta.hasOwnProperty(school_num)) {
            return []
        }
        if (!stored_meta[school_num].forms.forms.hasOwnProperty(form)) {
            return []
        }
        duplicated_courses_match[favourite] = {};
        for (const class_group of Object.keys(stored_meta[school_num].forms.forms[form].class_groups)) {
            if (favourites[favourite].preferences[class_group] === undefined) {
                favourites[favourite].preferences[class_group] = true;
            }
        }

        return sort_courses_by_subject(favourite, stored_meta[school_num].forms.forms[form].class_groups)
        //return Object.entries(stored_meta[school_num].forms.forms[form].class_groups);
    }

    function sort_courses_by_subject(favourite, obj) {
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
                    duplicated_courses_match[favourite][class_number] = obj.class_number;
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

</script>

<button on:click={save_favourites}>Speichern</button>
<button on:click={add_favourite}>Favorit hinzufügen</button>
{#each favourites as _, favourite}
    <p>
        <input type="text" bind:value={favourites[favourite].name}>
        <!-- TODO: GET AUTHORIZED SCHOOLS -->
        <select name="school_select" id="" bind:value={favourites[favourite].school_num} on:change={() => clear_favourite(favourite)}>
            <option value="10001329">Ostwald</option>
            <option value="10000000">Beispielschule</option>
        </select>
        <select name="plan_type_select" id="" bind:value={favourites[favourite].plan_type} on:change={() => favourites[favourite].plan_value = ""}>
            <option value="forms">Klassenplan</option>
            <option value="teachers">Lehrerplan</option>
            <option value="rooms">Raumplan</option>
            <option value="free_rooms">Freie Räume</option>
        </select>
        {#if favourites[favourite].plan_type === "forms"}
            <Select data={get_values(favourites[favourite].school_num, favourites[favourite].plan_type, all_meta)} grouped={true} bind:selected_id={favourites[favourite].plan_value} data_name="{favourites[favourite].plan_type}">Klasse/Lehrer/Raum auswählen</Select>
            <!--choosable courses-->
            {#each Object.entries(
                get_subjects(favourite, all_meta)
            ).sort(([subj1, _], [subj2, __]) => subj1.localeCompare(subj2)).sort(([_, courses1], [__, courses2]) => courses2.length - courses1.length) as [subject, courses]}
                {#if courses.length === 1}
                    <li>{subject}:<input
                            type="checkbox"
                            bind:checked={favourites[favourite].preferences[courses[0].class_number]}
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
                            <Button class="inline-flex" on:click={() => {
                                for (const course of courses) {
                                    favourites[favourite].preferences[course.class_number] = true;
                                }
                            }}>Alle Auswählen</Button>
                            <Button class="inline-flex" on:click={() => {
                                for (const course of courses) {
                                    favourites[favourite].preferences[course.class_number] = false;
                                }
                            }}>Keinen Auswählen</Button>
                        {/if}
                    </li>
                    <ul>
                        {#each courses as course}
                            <li>
                                <input
                                        type="checkbox"
                                        bind:checked={favourites[favourite].preferences[course.class_number]}
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



        {:else if favourites[favourite].plan_type !== "free_rooms"}
            <Select data={get_values(favourites[favourite].school_num, favourites[favourite].plan_type, all_meta)} grouped={false} bind:selected_id={favourites[favourite].plan_value} data_name="{favourites[favourite].plan_type}">Klasse/Lehrer/Raum auswählen</Select>
        {/if}
        <button on:click={() => {delete_favourite(favourite)}}>Favorit löschen</button>
    </p>
{/each}


<style lang="scss">

</style>