<script>
    import Lesson from './Lesson.svelte';
    import {onMount} from "svelte";
    import {replace_page} from "../../utils.js";
    import {title} from "../../stores.js";

    export let api_base;
    export let school_num;
    export let date;
    export let plan_type;
    export let plan_value;
    export let meta;
    export let show_title = true;
    export let extra_height = true;
    export let week_letter = "";
    export let all_rooms;
    export let selected_revision;
    export let enabled_dates;
    export let free_days;
    export let available_plan_version;

    onMount(() => {
        if(!school_num) {
            replace_page('school_manager');
        }
        title.set("Wochenplan");
    });

    let test_lesson = {
        "begin": "08:00",
        "class_number": "353",
        "current_class": "5Et12",
        "current_forms": [
            "5/1",
            "5/2"
        ],
        "current_forms_str": "5/1,2",
        "current_rooms": [
            "214"
        ],
        "current_teachers": [
            "CRL"
        ],
        "end": "09:30",
        "forms_changed": false,
        "info": [],
        "is_unplanned": false,
        "periods": [
            1,
            2
        ],
        "room_changed": false,
        "scheduled_class": "5Et12",
        "scheduled_forms": [
            "5/1",
            "5/2"
        ],
        "scheduled_forms_str": "5/1,2",
        "scheduled_rooms": [
            "214"
        ],
        "scheduled_teachers": [
            "CRL"
        ],
        "subject_changed": false,
        "takes_place": true,
        "teacher_changed": false
    };
</script>

Yippeee

<Lesson lesson={test_lesson} bind:plan_type bind:plan_value bind:date />

<style lang="scss">

</style>