<script>
    import Plan from "./Plan.svelte";
    import { onMount } from "svelte";
    import { title } from "./stores";

    onMount(() => {
        location.hash = "#weekplan";
        title.set("Wochenplan");
    });
    
    export let api_base;
    export let week_start;
    export let plan_type;
    export let plan_value;

    let weekdates = [];
    let week_letter = "";
    let plan_type_map = {
        "forms": "Klasse",
        "rooms": "Raum",
        "teachers": "Lehrer"
    };

    function getMonday(d) {
        d = new Date(d);
        var day = d.getDay(),
            diff = d.getDate() - day + (day == 0 ? -6:1); // adjust when day is sunday
        return new Date(d.setDate(diff));
    }
    function gen_weekdates(week_start) {
        let converted_week_start = new Date(getMonday(week_start));
        let tmp_new_date = null;
        weekdates = [];
        for (let i = 0; i < 5; i++) {
            tmp_new_date = new Date(converted_week_start.getTime() + (3600 * 1000 * 24 * i));
            weekdates.push(`${tmp_new_date.getFullYear()}-${('00'+(tmp_new_date.getMonth()+1)).slice(-2)}-${('00'+tmp_new_date.getDate()).slice(-2)}`);
        }
    }
    $: gen_weekdates(week_start);
</script>
<div class="responsive-heading">
    Wochenplan für {plan_type_map[plan_type]} <span class="custom-badge">{plan_value}</span> 
    in der Woche vom <span class="custom-badge">{week_start}</span> <span class="no-linebreak">({week_letter}-Woche)</span>
</div>
<div class="week_plan">
    <Plan bind:api_base date={weekdates[0]} bind:plan_type bind:plan_value show_title={false} extra_height={false} bind:week_letter />
    <Plan bind:api_base date={weekdates[1]} bind:plan_type bind:plan_value show_title={false} extra_height={false} />
    <Plan bind:api_base date={weekdates[2]} bind:plan_type bind:plan_value show_title={false} extra_height={false} />
    <Plan bind:api_base date={weekdates[3]} bind:plan_type bind:plan_value show_title={false} extra_height={false} />
    <Plan bind:api_base date={weekdates[4]} bind:plan_type bind:plan_value show_title={false} extra_height={false} />
</div>
<style lang="scss">
    .week_plan {
        display: flex;
        flex-direction: row;
        gap: 10px;
        width: 100%;
        overflow: scroll;
    }
    .responsive-heading {
        font-size: clamp(1.063rem, 4vw, 2.28rem);
        line-height: 1.6;
        margin-bottom: 15px;
    }
</style>