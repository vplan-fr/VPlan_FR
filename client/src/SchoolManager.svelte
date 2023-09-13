<script>
    import {notifications} from './notifications.js';
    import { onMount } from "svelte";
    import { current_page, title } from "./stores";
    import {customFetch} from "./utils.js";
    import Select from "./Components/Select.svelte";
    import { fly } from 'svelte/transition';

    onMount(() => {
        location.hash = "#school_manager";
        title.set("Schule wählen");
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
                authorized_school_ids = [...authorized_school_ids, authorize_school_id];
            })
            .catch(error => {
                notifications.danger(error);
            }
        );
    }

    function navigate_page(page_id) {
        $current_page = page_id;
        location.hash = `#${page_id}`;
    }

    get_schools();
    get_authorized_schools();
    get_admin_status();
    //$: console.log(schools);
    // $: console.log(authorized_school_ids);
</script>

<main style="position: relative;">
    {#if !school_auth_visible}
    <div transition:fly|local={{x: -600}} class="absolute-position">
        <h1 class="responsive-heading">Schulauswahl</h1>
        <span class="responsive-text">Moin, bitte wähle hier deine Schule aus:</span>
        <Select data={schools} icon_location="/base_static/images/school_icons" bind:selected_elem={authorize_school_id}>Schule auswählen</Select>
        <button class="button" on:click={() => {
            if (authorize_school_id) {
                console.log(authorized_school_ids);
                console.log(is_admin)
                if(isObjectInList(authorize_school_id, authorized_school_ids) || is_admin) {
                    school_num = authorize_school_id;
                    navigate_page("plan");
                } else {
                    school_auth_visible = true;
                }
            } else {
                notifications.danger("Wähle eine Schule aus um fortzufahren.");
            }
        }}>Weiter zur Schule <span class="material-symbols-outlined">keyboard_arrow_right</span></button>
    </div>
    {:else}
    <div transition:fly|local={{x: 600}} class="absolute-position">
        <button on:click={() => {school_auth_visible = false;}} type="reset" id="back_button">←</button>
        <input bind:value={authorize_school_id}>
        <input bind:value={username}>
        <input type="password" bind:value={password}>
        <button on:click={authorize_school}>Authorize School</button>
    </div>
    {/if}
</main>

<style lang="scss">
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
        border: none;
        background-color: var(--accent-color);
        color: var(--text-color);
        border-radius: 5px;
        padding: 10px;
        font-size: 1rem;
        position: relative;
        padding-right: .5em;

        .material-symbols-outlined {
            font-size: 1.3em;
            float: right;
            margin-left: .5em;
        }
    }
</style>

