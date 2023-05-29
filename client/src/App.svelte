<script>
    import Plan from "./Plan.svelte";
    import { onMount } from 'svelte';

    let school_num = "10001329";
    let date = "2023-06-01";
    let plan_type = "rooms";
    let plan_value = "110";
    let teacher_list = [];
    let api_base;
    $: api_base = `./api/v69.420/${school_num}`;

    let selected_teacher;
    let selected_room;
    $: console.log(selected_room);
    let meta = {};
    function get_meta(api_base) {
        fetch(`${api_base}/meta`)
            .then(response => response.json())
            .then(data => {
                meta = data;
            })
            .catch(error => {
                console.error(error);
        });
    }
    $: get_meta(api_base);
    $: teacher_list = (Object.keys(meta).length !== 0) ? Object.keys(meta["teachers"]) : [];
</script>

<main>
    <input id="inp_school_num" type="text" bind:value={school_num}>
    <br>
    <div class="input-field" id="room-select">
        <label for="rooms">Select a Room:</label>
        <select name="rooms" id="rooms" bind:value={selected_room}
            on:change="{() => {plan_type = "rooms"; plan_value = selected_room}}">
            {#each meta["rooms"] || [] as room}
                <option value="{room}">{room}</option>
            {/each}
        </select>
    </div>
    <div class="input-field" id="teacher-select">
        <label for="teachers">Select a Teacher:</label>
        <select name="teachers" id="teachers" bind:value={selected_teacher}
            on:change="{() => {plan_type = "teachers"; plan_value = selected_teacher}}">
            {#each teacher_list as teacher}
                <option value="{teacher}">{teacher}</option>
            {/each}
        </select>
    </div>
    <br>
    <br>
    <Plan bind:api_base bind:date bind:plan_type bind:plan_value bind:meta />
	<!-- <span class="material-symbols-outlined">settings</span> -->
</main>

<style lang="scss">
    main {
        margin: 0 auto;
        max-width: 1280px;
        width: 90%;
        @media only screen and (min-width: 601px) {
            width: 85%;
        }
        @media only screen and (min-width: 993px) {
            width: 70%;
        }
        @media only screen and (max-width: 500px) {
            width: 95%;
        }
    }
</style>