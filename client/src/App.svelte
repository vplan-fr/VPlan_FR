<script>
    import Plan from "./Plan.svelte";
    import Authentication from "./Authentication.svelte";
    import {DatePicker} from 'attractions';
    import {group_rooms} from "./utils.js";
	import Toast from './Toast.svelte';
    import {notifications} from './notifications.js';

    let school_num = localStorage.getItem('school_num');
    let date = null;
    let plan_type = "forms";
    let plan_value = "10/3";
    let teacher_list = [];
    let all_rooms;
    let grouped_forms = [];
    let api_base;
    $: api_base = `./api/v69.420/${school_num}`;
    let logged_in = localStorage.getItem('logged_in') === 'true';
    check_login_status();

    const pad = (n, s = 2) => (`${new Array(s).fill(0)}${n}`).slice(-s);

    let selected_teacher;
    let selected_room;
    let selected_form;
    let meta = {};
    let disabledDates = [];
    let enabled_dates = [];
    let grouped_rooms = [];
    let error_hidden;
    let error_message;

    $: if (all_rooms) {
        grouped_rooms = group_rooms(all_rooms);
    }

    function get_meta(api_base) {
        if (!logged_in) {
            return;
        }
        fetch(`${api_base}/meta`)
            .then(response => response.json())
            .then(data => {
                meta = data.meta;
                all_rooms = data.rooms;
                teacher_list = Object.keys(data.teachers);
                grouped_forms = data.forms.grouped_forms;
                enabled_dates = Object.keys(data.dates);
                date = data.date;
                console.log(data);
            })
            .catch(error => {
                notifications.danger("Metadata-fetch fehlgeschlagen, Server nicht erreichbar!", 2000);
            });
    }

    function update_disabled_dates(enabled_dates) {
        if (!logged_in) {
            return;
        }
        let tmp_start = new Date(enabled_dates[enabled_dates.length - 1]);
        let tmp_end = new Date(enabled_dates[0]);
        tmp_start.setDate(tmp_start.getDate() + 1);
        tmp_end.setDate(tmp_end.getDate() - 1);
        disabledDates = [
            {start: new Date("0"), end: tmp_end},
            {start: tmp_start, end: new Date("9999")},
        ];
        for (let i = 0; i < enabled_dates.length; i++) {
            tmp_start = new Date(enabled_dates[i]);
            tmp_end = new Date(enabled_dates[i + 1]);
            tmp_start.setDate(tmp_start.getDate() + 1);
            tmp_end.setDate(tmp_end.getDate() - 1);
            disabledDates.push({
                start: tmp_start,
                end: tmp_end
            });
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
                notifications.danger("Login-Check fehlgeschlagen, Server nicht erreichbar!", 2000);
            }
        );
    }

    function logout() {
        fetch('/logout')
            .then(response => response.json())
            .then(data => {
                logged_in = !data["success"];
                localStorage.setItem('logged_in', `${logged_in}`);
                if (logged_in) {
                    error_hidden = false;
                    error_message = data["error"];
                }
            })
            .catch(error => {
                notifications.danger("Logout fehlgeschlagen, Server nicht erreichbar!", 2000);
            });
    }

    $: logged_in, get_meta(api_base);
    $: logged_in, update_disabled_dates(enabled_dates);

    // Popup for school authorization
    import SchoolAuthorization from './SchoolManager.svelte';
    let isPopupVisible = false;
    function togglePopup() {
        isPopupVisible = !isPopupVisible;
    }
</script>

{#if logged_in}
<nav>
    <button on:click={logout}>Logout</button>
    <button on:click={togglePopup}>Manage Schools</button>
</nav>
{/if}
<main>
    <div id="auth-wrapper">
        {#if isPopupVisible}
            <SchoolAuthorization bind:api_base bind:school_num={school_num} isPopupVisible={isPopupVisible} on:close={togglePopup}/>
        {/if}
    </div>

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
                    on:change={() => {plan_type = 'rooms'; plan_value = selected_room}}>
                {#each grouped_rooms as [category, rooms]}
                    <optgroup label={category}>
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
                    on:change={() => {plan_type = 'teachers'; plan_value = selected_teacher}}>
                {#each teacher_list as teacher}
                    <option value={teacher}>{teacher}</option>
                {/each}
            </select>
        </div>
        <div class="input-field" id="form-select">
            <label for="forms">Wähle eine Klasse aus:</label>
            <select name="forms" id="forms" bind:value={selected_form}
                    on:change={() => {plan_type = 'forms'; plan_value = selected_form}}>
                {#each Object.entries(grouped_forms) as [form_group, forms]}
                    <optgroup label={form_group}>
                        {#each forms as form}
                            <option value="{form}">{form}</option>
                        {/each}
                    </optgroup>
                {/each}
            </select>
        </div>
        <br>
        <br>
        <Plan bind:api_base bind:date bind:plan_type bind:plan_value bind:all_rooms/>
        <!-- <Weekplan bind:api_base bind:week_start={date} bind:plan_type bind:plan_value /> -->
    {:else}
        <Authentication bind:logged_in></Authentication>
    {/if}
</main>
<Toast />

<style lang="scss">
    nav {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 20px;
        overflow: hidden;
        position: fixed;
        top: 0;
        width: 100%;
    }

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
    #auth-wrapper {
        z-index: 10;
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