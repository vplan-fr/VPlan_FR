<script>
    import Plan from "./Plan.svelte";
    import { onMount } from 'svelte';

    let school_num = "10001329";
    let date = "2023-05-23";
    let plan_type = "room_plan";
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
            on:change="{() => {plan_type = "room_plan"; plan_value = selected_room}}">
            {#each meta["rooms"] || [] as room}
                <option value="{room}">{room}</option>
            {/each}
        </select>
    </div>
    <div class="input-field" id="teacher-select">
        <label for="teachers">Select a Teacher:</label>
        <select name="teachers" id="teachers" bind:value={selected_teacher}
            on:change="{() => {plan_type = "teacher_plan"; plan_value = selected_teacher}}">
            {#each teacher_list as teacher}
                <option value="{teacher}">{teacher}</option>
            {/each}
        </select>
    </div>
    <br>
    <br>
    <Plan bind:api_base bind:date bind:plan_type bind:plan_value bind:meta />
	<span class="material-symbols-outlined">settings</span>
    Lorem<br>ipsum<br>dolor<br>sit<br>amet<br>consectetur<br>adipisicing<br>elit.<br>Commodi<br>officia<br>natus<br>ad,<br>aut<br>accusantium<br>dolores<br>totam<br>veritatis<br>placeat<br>eligendi<br>repudiandae,<br>fugiat<br>facere<br>veniam<br>non<br>fugit<br>fuga<br>temporibus<br>optio<br>ex<br>deserunt.
    Lorem<br>ipsum<br>dolor<br>sit<br>amet<br>consectetur<br>adipisicing<br>elit.<br>Commodi<br>officia<br>natus<br>ad,<br>aut<br>accusantium<br>dolores<br>totam<br>veritatis<br>placeat<br>eligendi<br>repudiandae,<br>fugiat<br>facere<br>veniam<br>non<br>fugit<br>fuga<br>temporibus<br>optio<br>ex<br>deserunt.
</main>

<style lang="scss">
    .select-wrapper {
        background-color: white;
        color: black;
        select {
            option {
                color: black !important;
            }
        }
    }
</style>