<script>
    import {notifications} from './notifications.js';
    import { onMount } from "svelte";
    import { title } from "./stores";
    import {customFetch, navigate_page} from "./utils.js";
    import Select from "./Components/Select.svelte";
    import { fly } from 'svelte/transition';

    onMount(() => {
        location.hash = "#school_manager";
        title.set("Schule wählen");
        get_schools();
        get_authorized_schools();
        get_admin_status();
    });
    
    export let school_num;
    function isObjectInList(object, list) {
        return list.some(item => item.toString() === object.toString());
    }

    let authorize_school_id;
    let username = "schueler";
    let password = "";
    let schools = {};
    let authorized_school_ids = [];
    let school_auth_visible = false;
    let is_admin = false;
    let schools_arr = [];

    function get_schools() {
        customFetch("/api/v69.420/schools")
            .then(data => {
                schools = data;
                // console.log(data);
            })
            .catch(error => {
                notifications.danger(error);
            })
    }

    function get_authorized_schools() {
        customFetch("/auth/authorized_schools")
            .then(data => {
                authorized_school_ids = data;
            })
            .catch(error => {
                notifications.danger(error)
            }
        );
    }
    
    function get_admin_status() {
        customFetch("/auth/is_admin")
            .then(data => {
                is_admin = data;
            })
            .catch(error => {
                notifications.danger(error)
            }
        );
    }

    function authorize_school() {
        get_authorized_schools();
        console.log(username, password);
        if (!isObjectInList(authorize_school_id, Object.keys(schools))) {
            notifications.danger("Schule unbekannt (kontaktiere uns, um deine Schule hinzuzufügen)")
            return
        }
        if (username === "") {
            notifications.danger("Bitte gib einen Nutzernamen an");
            return
        }
        if (password === "") {
            notifications.danger("Bitte gib ein Passwort an");
            return
        }
        let formData = new FormData();
        formData.append('username', username);
        formData.append('pw', password);
        let tmp_api_base = `/api/v69.420/${authorize_school_id}`;
        customFetch(`${tmp_api_base}/authorize`, {
            method: 'POST',
            body: formData
        })
            .then(data => {
                notifications.success("Schule wurde autorisiert");
                school_num = authorize_school_id;
                localStorage.setItem("school_num", school_num);
                authorized_school_ids = [...authorized_school_ids, authorize_school_id];
                navigate_page('plan');
            })
            .catch(error => {
                notifications.danger(error);
            }
        );
    }

    function update_schools_arr(schools) {
        schools_arr = [];
        for(let [school_id, content] of Object.entries(schools)) {
            schools_arr.push({"id": school_id, "name": content["name"], "icon": content["icon"]});
        }
    }

    // $: console.log(schools);
    $: update_schools_arr(schools);
</script>

<main>
    {#if !school_auth_visible}
    <form transition:fly|local={{x: -600}} on:submit|preventDefault={() => {
            if (authorize_school_id) {
                if(isObjectInList(authorize_school_id, authorized_school_ids) || is_admin) {
                    school_num = authorize_school_id;
                    localStorage.setItem("school_num", school_num);
                    navigate_page("plan");
                } else {
                    school_auth_visible = true;
                }
            } else {
                notifications.danger("Wähle eine Schule aus um fortzufahren.");
            }
        }}>
        <h1 class="responsive-heading">Schulauswahl</h1>
        <span class="responsive-text">Moin, bitte wähle hier deine Schule aus:</span>
        <Select data={schools_arr} icon_location="/public/base_static/images/school_icons" bind:selected_id={authorize_school_id}>Schule auswählen</Select>
        <button class="button" type="submit">Weiter zur Schule <span class="material-symbols-outlined">keyboard_arrow_right</span></button>
    </form>
    {:else}
    <form transition:fly|local={{x: 600}} on:submit|preventDefault={authorize_school}>
        <button on:click={() => {school_auth_visible = false;}} type="reset" id="back_button">←</button>
        <h1 class="responsive-heading">{authorize_school_id ? schools[authorize_school_id]["name"] : "Schul"}-Login</h1>
        <span class="responsive-text">Trage hier die Zugangsdaten für deine Schule ein<br>(dieselben wie in der <div title="🤢" style="display: inline-block;">VpMobil24-App</div>)</span>
        <label for="school_username">Nutzername</label>
        <div class="input_icon">
            <img src="/public/base_static/images/user-solid-white.svg" alt="User Icon">
            <input disabled={!school_auth_visible} autocomplete="off" name="school_username" bind:value={username} type="text" required class="textfield" placeholder="Nutzername"/>
        </div>
        <label for="school_password">Passwort</label>
        <div class="input_icon">
            <img src="/public/base_static/images/lock-solid-white.svg" alt="Lock Icon">
            <input disabled={!school_auth_visible} autocomplete="off" name="school_password" bind:value={password} type="password" required class="textfield" placeholder="Passwort"/>
        </div>
        <button class="button" type="submit">Login</button>
    </form>
    {/if}
</main>

<style lang="scss">
    form {
        position: absolute;
        top: 50%;
        left: calc(50% + (100vw - 100%) / 2);
        transform: translate(-50%, -50%);
        display: flex;
        flex-direction: column;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 5px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        min-width: min(400px, 75vw);
    }

    label {
        margin-bottom: 8px;
        font-size: var(--font-size-base);
    }

    .input_icon {
        position: relative;
        margin-bottom: 5px;

        .textfield {
            font-size: var(--font-size-sm);
            padding-left: 40px;
        }
        img {
            position: absolute;
            top: 14px;
            left: 12px;
            width: 20px;
            height: 20px;
            background-size: contain;
            z-index: 1;
        }
    }

    .textfield {
        width: 100%;
        padding: 12px 20px;
        margin-bottom: 8px;
        box-sizing: border-box;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background-color: rgba(255, 255, 255, 0.1);
        color: var(--text-color);
        border-radius: 5px;
    }

    .absolute-position {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
    }

    .responsive-heading {
        margin-bottom: 10px;
    }

    .responsive-text {
        display: block;
        margin-bottom: 15px;
    }

    .button {
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        border: none;
        background-color: var(--accent-color);
        color: var(--text-color);
        border-radius: 5px;
        padding: .5em;
        margin: 1px;
        margin-top: 15px;
        font-size: var(--font-size-base);
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

    #back_button {
        position: absolute;
        top: 0px;
        left: 5px;
        border: 0;
        background: none;
        color: var(--text-color);
        font-size: var(--font-size-md);
    }
</style>

