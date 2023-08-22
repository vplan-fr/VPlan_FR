<script>
    import Plan from "./Plan.svelte";
    import Weekplan from "./Weekplan.svelte";
    import Authentication from "./Authentication.svelte";
    import { onMount } from 'svelte';
    import { DatePicker } from 'attractions';

    let school_num = "10001329";
    let date = null;
    let plan_type = "forms";
    let plan_value = "10/3";
    let teacher_list = [];
    let rooms;
    let grouped_forms = [];
    let api_base;
    $: api_base = `./api/v69.420/${school_num}`;
    let logged_in = localStorage.getItem('logged_in') === 'true';
    check_login_status();

    const pad = (n,s=2) => (`${new Array(s).fill(0)}${n}`).slice(-s);

    let selected_teacher;
    let selected_room;
    let selected_form;
    let meta = {};
    let disabledDates = [];
    let enabled_dates = [];

    let grouped_rooms = [];
    $: {
        if (rooms) {
            let _grouped_rooms = {};
            for (let [room, data] of Object.entries(rooms)) {
                let category = JSON.stringify([data.house, data.floor]);

                if (_grouped_rooms[category] === undefined) {
                    _grouped_rooms[category] = [];
                }
                _grouped_rooms[category].push(room);
            }

            grouped_rooms = Object.entries(_grouped_rooms).map(([category, rooms]) => [JSON.parse(category), rooms]);

            let sort_key = (house, floor) => {
                if (house === null) {
                    return 1000;
                }
                if (typeof house === "string") {
                    house = house.charCodeAt(0);
                }
                if (floor === null) {
                    floor = 10;
                }
                return house*10 + floor;
            }

            grouped_rooms.sort(([[house1, floor1], _], [[house2, floor2], __]) => {
                return sort_key(house1, floor1) - sort_key(house2, floor2);
            });
            grouped_rooms.map(([_, rooms]) => rooms.sort((room1, room2) => rooms[room1]?.room_nr - rooms[room2]?.room_nr));

            function get_category_name([house, floor]) {
                let out = "";
                if (house !== null) {
                    out += `Haus ${house}`;
                }
                if (floor !== null) {
                    out += ` / Etage ${floor}`;
                }
                if (out.length === 0) {
                    out = "Sonstige";
                }
                return out;
            }

            grouped_rooms = grouped_rooms.map(([category, rooms]) => [get_category_name(category), rooms]);
        }
    }
    
    function get_meta(api_base) {
        if (!logged_in) {
            return;
        }
        fetch(`${api_base}/meta`)
            .then(response => response.json())
            .then(data => {
                meta = data.meta;
                rooms = data.rooms;
                teacher_list = Object.keys(data.teachers);
                grouped_forms = data.forms.grouped_forms;
                enabled_dates = Object.keys(data.dates);
                date = data.date;
                console.log(data);
            })
            .catch(error => {
                console.error(error);
            }
        );
    }
    function update_disabled_dates(enabled_dates) {
        if (!logged_in) {
            return;
        }
        let tmp_start = new Date(enabled_dates[enabled_dates.length-1]);
        let tmp_end = new Date(enabled_dates[0]);
        tmp_start.setDate(tmp_start.getDate() + 1);
        tmp_end.setDate(tmp_end.getDate() - 1);
        disabledDates = [
            {start: new Date("0"), end: tmp_end},
            {start: tmp_start, end: new Date("9999")},
        ];
        for(let i = 0; i < enabled_dates.length; i++) {
            tmp_start = new Date(enabled_dates[i]);
            tmp_end = new Date(enabled_dates[i+1]);
            tmp_start.setDate(tmp_start.getDate() + 1);
            tmp_end.setDate(tmp_end.getDate() - 1);
            disabledDates.push({
                start: tmp_start,
                end: tmp_end
            })
        }
    }

    function check_login_status() {
        fetch('/check_login')
            .then(response => response.json())
            .then(data => {
                logged_in = data["logged_in"];
                localStorage.setItem('logged_in', `${logged_in}`);
            })
            .catch(error => {
                console.error(error);
            }
        );
    }

    // onMount(() => {
    //     document.querySelector('.date-picker .handle input').setAttribute("readonly", "true");
    // });

    $: logged_in, get_meta(api_base);
    $: logged_in, update_disabled_dates(enabled_dates);
</script>

<main>
    {#if logged_in}
        <DatePicker 
            format="%Y-%m-%d" 
            locale="de-DE" 
            closeOnSelection 
            bind:disabledDates 
            value={(date === null) ? null : new Date(date)}
            on:change={(evt) => {
                let tmp_dat = evt.detail.value;
                date = `${tmp_dat.getFullYear()}-${pad(tmp_dat.getMonth()+1)}-${pad(tmp_dat.getDate())}`;
            }}
        />
        <input id="inp_school_num" type="text" bind:value={school_num}>
        {date}
        <br>
        <div class="input-field" id="room-select">
            <label for="rooms">Wähle einen Raum aus:</label>
            <select name="rooms" id="rooms" bind:value={selected_room}
                on:change="{() => {plan_type = 'rooms'; plan_value = selected_room}}">
                {#each grouped_rooms as [category, rooms]}
                    <optgroup label="{category}">
                    {#each rooms as room}
                        <option value="{room}">{room}</option>
                    {/each}
                    </optgroup>
                {/each}
            </select>
        </div>
        <div class="input-field" id="teacher-select">
            <label for="teachers">Wähle einen Lehrer aus:</label>
            <select name="teachers" id="teachers" bind:value={selected_teacher}
                on:change="{() => {plan_type = 'teachers'; plan_value = selected_teacher}}">
                {#each teacher_list as teacher}
                    <option value="{teacher}">{teacher}</option>
                {/each}
            </select>
        </div>
        <div class="input-field" id="form-select">
            <label for="forms">Wähle eine Klasse aus:</label>
            <select name="forms" id="forms" bind:value={selected_form}
                on:change="{() => {plan_type = 'forms'; plan_value = selected_form}}">
                {#each Object.entries(grouped_forms) as [form_group, forms]}
                    <optgroup label="{form_group}">
                    {#each forms as form}
                        <option value="{form}">{form}</option>
                    {/each}
                    </optgroup>
                {/each}
            </select>
        </div>
        <br>
        <br>
        <Plan bind:api_base bind:date bind:plan_type bind:plan_value />
        <!-- <Weekplan bind:api_base bind:week_start={date} bind:plan_type bind:plan_value /> -->
    {:else}
        <Authentication bind:logged_in></Authentication>
    {/if}
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
    :global {
        ul {
            padding-left: 30px !important;
            @media only screen and (max-width: 601px) {
                padding-left: 22px !important;
            }
            list-style-type: disc !important;
        }
    }
</style>