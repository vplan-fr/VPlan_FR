<script>
    import {notifications} from '../notifications.js';
    import { onMount } from "svelte";
    import {settings, title} from "../stores";
    import {customFetch, navigate_page, update_hash} from "../utils.js";
    import Select from "../base_components/Select.svelte";
    import { fly } from 'svelte/transition';
    import Button from '../base_components/Button.svelte';
    
    export let school_num;
    export let date;
    export let plan_type;
    export let plan_value;

    let authorize_school_id;
    let authorize_school_data = {};
    let username = "schueler";
    let password = "";
    let schools = [];
    let authorized_schools = [];
    let unauthorized_schools = [];
    let schools_categorized = {};
    let authorized_school_ids = [];
    let school_auth_visible = false;
    let is_admin = false;
    let school_id_arr = [];
    let password_visible = false;

    let school_add_visible = false;
    let add_school_name = "";
    let add_school_num = "";
    let add_school_username = "";
    let add_school_password = "";

    function isObjectInList(object, list) {
        return list.some(item => item.toString() === object.toString());
    }

    function get_schools() {
        customFetch("/api/v69.420/schools")
            .then(data => {
                schools = data;
                // put schools into form that works with the Select
                schools = schools.map(obj => {
                    const { _id, display_name, ...rest } = obj;
                    return { id: _id, display_name: display_name, ...rest };
                });
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
            }
        );
    }
    
    function get_admin_status() {
        customFetch("/auth/is_admin")
            .then(data => {
                is_admin = data;
            })
            .catch(error => {
                console.error("Admin-Status konnte nicht überprüft werden.");
            }
        );
    }

    function authorize_school() {
        get_authorized_schools();
        if (!isObjectInList(authorize_school_id, school_id_arr)) {
            notifications.danger("Schule unbekannt (kontaktiere uns, um deine Schule hinzuzufügen)")
            return
        }
        if (authorize_school_data.creds_needed) {
            if (username === "") {
                notifications.danger("Bitte gib einen Nutzernamen an");
                return
            }
            if (password === "") {
                notifications.danger("Bitte gib ein Passwort an");
                return
            }
        } else {
            username = "";
            password = "";
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
                if(school_num !== authorize_school_id) {
                    date = null;
                    plan_type = null;
                    plan_value = null;
                }
                school_num = authorize_school_id;
                localStorage.setItem("school_num", school_num);
                authorized_school_ids = [...authorized_school_ids, authorize_school_id];
                navigate_page($settings.weekplan_default ? "weekplan" : "plan");
            })
            .catch(error => {
                notifications.danger(error.message);
            }
        );
    }

    function get_school_by_id(school_id) {
        if (!school_id) {
            return {};
        }
        for (let school of schools) {
            if (school.id === school_id.toString()) {
                return school
            }
        }
        return {};
    }

    get_schools();
    get_authorized_schools();
    get_admin_status();
    
    onMount(() => {
        update_hash("school_manager");
        title.set("Schule wählen");
    });

    $: schools, school_id_arr = schools.map(obj => obj.id);
    $: schools, authorized_schools = schools.filter(obj => authorized_school_ids.includes(obj.id));
    $: schools, unauthorized_schools = schools.filter(obj => !authorized_school_ids.includes(obj.id));
    $: schools_categorized = [
        ["Autorisiert", authorized_schools],
        ["Unautorisiert", unauthorized_schools]
    ];
    $: authorize_school_data = get_school_by_id(authorize_school_id);

    function add_school() {

        let formData = new FormData();
        formData.append('display_name', add_school_name);
        formData.append('school_num', add_school_num);
        formData.append('username', add_school_username);
        formData.append('pw', add_school_password);
        let tmp_api_base = `/api/v69.420/${authorize_school_id}`;
        customFetch(`/api/v69.420/add_school`, {
            method: 'POST',
            body: formData
        })
            .then(data => {
                notifications.success(data);
                school_add_visible = false;
                add_school_name = "";
                add_school_num = "";
                add_school_username = "";
                add_school_password = "";
            })
            .catch(error => {
                notifications.danger(error.message);
            });
    }
    let auth_btn_disabled = false;
</script>

<svelte:head>
    <style>
        #page-container {
            overflow-x: unset !important;
        }
    </style>
</svelte:head>

<main>
    {#if !school_auth_visible && !school_add_visible}
    <form transition:fly|local={{x: -600}} on:submit|preventDefault={() => {
            if (authorize_school_id) {
                if(isObjectInList(authorize_school_id, authorized_school_ids) || is_admin) {
                    if(school_num !== authorize_school_id) {
                        date = null;
                        plan_type = null;
                        plan_value = null;
                    }
                    school_num = authorize_school_id;
                    localStorage.setItem("school_num", school_num);
                    navigate_page($settings.weekplan_default ? "weekplan" : "plan");
                } else {
                    school_auth_visible = true;
                }
            } else {
                notifications.danger("Wähle eine Schule aus um fortzufahren.");
            }
        }}>
        <h1 class="responsive-heading">Schulauswahl</h1>
        <span class="responsive-text">Moin, bitte wähle hier deine Schule aus:</span>
        <Select data={schools_categorized} grouped={true} icon_location="/public/base_static/images/school_icons" bind:selected_id={authorize_school_id} data_name="Schulen">Schule auswählen</Select>
        <span class="school-missing">Ist deine Schule nicht dabei? <button on:click={() => {school_add_visible = true;}} class="link-button" type="button">Füge sie hinzu</button></span>
        <Button type="submit" background="var(--accent-color)">Weiter zur Schule <span class="material-symbols-outlined">keyboard_arrow_right</span></Button>
        {#if is_admin}
        <Button type="button" on:click={() => {
            if (authorize_school_id) {
                school_auth_visible = true;
            } else {
                notifications.danger("Wähle eine Schule aus um fortzufahren.");
            }
        }}>Schule autorisieren <span class="material-symbols-outlined">login</span></Button>
        {/if}
    </form>
    {:else if !school_add_visible}
    <form transition:fly|local={{x: 600}} on:submit|preventDefault={authorize_school}>
        <button on:click={() => {school_auth_visible = false;}} type="reset" id="back_button">
            <span class="material-symbols-outlined">keyboard_backspace</span>
        </button>
        <h1 class="responsive-heading">{authorize_school_id ? authorize_school_data.display_name : "Schul"}-Login</h1>
        {#if authorize_school_data.creds_needed}
            <span class="responsive-text">Trage hier die Zugangsdaten <strong>für deine Schule</strong> ein, <strong>nicht die deines Accounts</strong>.<br>(dieselben wie in der <div title="🤢" style="display: inline-block;">VpMobil24-App</div>)</span>
            <label for="school_username">Nutzername</label>
            <div class="input_icon">
                <img src="/public/base_static/images/user-solid-white.svg" alt="User Icon">
                <input disabled={!school_auth_visible} autocomplete="off" name="school_username" bind:value={username} type="text" required class="textfield" placeholder="Nutzername"/>
            </div>
            <label for="school_password">Schul-Passwort</label>
            <div class="input_icon password_field">
                <img src="/public/base_static/images/lock-solid-white.svg" alt="Lock Icon">
                <button type="button" on:click={() => {password_visible = !password_visible}} tabindex="-1">
                    <span class="material-symbols-outlined">{password_visible ? "visibility_off" : "visibility"}</span>
                </button>
                <input disabled={!school_auth_visible} autocomplete="off" name="school_password" on:input={(event) => {
                    password = event.target.value;
                    // if autofilled, warn user that they're probably trying the wrong password
                    if(window.getComputedStyle(event.target, ":-webkit-autofill").getPropertyValue("background-color") !== "rgba(255, 255, 255, 0.1)") {
                        auth_btn_disabled = true;
                        notifications.warning("Denk daran, dass nicht dein Accountpasswort gefragt ist ;)", 4000);
                        setTimeout(function(){auth_btn_disabled = false;}, 4000);
                    }
                }} type={password_visible ? "text" : "password"} required class="textfield" placeholder="Schul-Passwort"/>
            </div>
        {:else}
            <span class="responsive-text">(Für diese Schule benötigst du keine Zugangsdaten)</span>
        {/if}
        <Button type="submit" background="var(--accent-color)" disabled={auth_btn_disabled}>Autorisieren</Button>
    </form>
    {:else}
        <form transition:fly|local={{x: 600}} on:submit|preventDefault={add_school} autocomplete="off">
            <button on:click={() => {school_add_visible = false;}} type="reset" id="back_button">
                <span class="material-symbols-outlined">keyboard_backspace</span>
            </button>
            <h1 class="responsive-heading">Schule hinzufügen</h1>
            <label for="add_school_name">Name der Schule</label>
            <input disabled={!school_add_visible} autocomplete="organization" name="add_school_name" bind:value={add_school_name} type="text" required class="textfield" placeholder="Name der Schule (z.B. Max-Mustermann-Gymnasium Löbau)"/>
            <label for="add_school_num">Schulnummer</label>
            <input disabled={!school_add_visible} autocomplete="off" name="add_school_num" bind:value={add_school_num} type="text" required class="textfield" placeholder="Schulnummer (z.B. 10000000)"/>
            <label for="add_school_username">Nutzername</label>
            <div class="input_icon">
                <img src="/public/base_static/images/user-solid-white.svg" alt="User Icon">
                <input disabled={!school_add_visible} autocomplete="username" name="add_school_username" bind:value={add_school_username} type="text" required class="textfield" placeholder="Nutzername (schueler/lehrer)"/>
            </div>
            <label for="add_school_password">Schul-Passwort</label>
            <div class="input_icon password_field">
                <img src="/public/base_static/images/lock-solid-white.svg" alt="Lock Icon">
                <input disabled={!school_add_visible} autocomplete="new-password" name="add_school_password" on:input={(event) => {add_school_password = event.target.value}} type={password_visible ? "text" : "password"} required class="textfield" placeholder="Schul-Passwort"/>
            </div>
            <Button type="submit" background="var(--accent-color)">Hinzufügen</Button>
        </form>
    {/if}
</main>

<style lang="scss">
    strong {
        font-weight: 700;
    }

    .password_field {
        .textfield {
            padding-right: 40px;
        }

        button {
            position: absolute;
            top: 0;
            right: 0;
            width: 40px;
            height: 48px;
            z-index: 1;
            border: none;
            background: transparent;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            padding-left: 5.5px;

            .material-symbols-outlined {
                color: var(--text-color);
                font-size: 25px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
        }
    }

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
        font-size: var(--font-size-sm);
    }

    .responsive-heading {
        margin-bottom: 10px;
    }

    .responsive-text {
        display: block;
        margin-bottom: 15px;
    }

    #back_button {
        position: absolute;
        top: 5px;
        left: 5px;
        padding: 0;
        border: 0;
        background: none;
        color: var(--text-color);
        font-size: var(--font-size-md);
    }

    .school-missing {
        font-size: var(--font-size-base);
        margin-bottom: 5px;
    }

    .link-button {
        display: inline-block;
        text-align: left;
        padding: 0;
        margin: 0;
        color: var(--accent-color);
        background: transparent;
        border: 0;
        font-size: var(--font-size-base);
    }
</style>

