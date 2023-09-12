<script>
    import {notifications} from './notifications.js';
    import { onMount } from "svelte";
    import { title } from "./stores";
    import {customFetch} from "./utils.js";

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
    let authorization_message = "Nothing to show";
    let schools = {};
    let authorized_school_ids = [];
    function get_schools() {
        customFetch("/api/v69.420/schools")
            .then(data => {
                schools = data;
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
    function authorize_school() {
        get_authorized_schools();
        console.log(username, password);
        if (!isObjectInList(authorize_school_id, Object.keys(schools))) {
            authorization_message = "School doesnt exist...";
            return
        }
        if (username === "") {
            authorization_message = "No username provided";
            return
        }
        if (password === "") {
            authorization_message = "No password provided";
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
                authorization_message = "Success!!!"
                authorized_school_ids = [...authorized_school_ids, authorize_school_id];
            })
            .catch(error => {
                notifications.danger(error);
            }
        );
    }
    get_schools();
    get_authorized_schools();
    //$: console.log(schools);
    //$: console.log(authorized_school_ids);
</script>



<main>
    <div>
        {#each authorized_school_ids as school_id}
            <p>{schools[school_id]["name"]}<button on:click={() => {
                school_num = school_id;
                localStorage.setItem('school_num', `${school_num}`)
            }}>Choose</button></p>
        {/each}
    </div>
    <div>
        {#each Object.keys(schools) as school_id}
            {#if !isObjectInList(school_id, authorized_school_ids)}
                <p>
                    {schools[school_id]["name"]} ({school_id})
                    <button on:click={() => authorize_school_id=school_id}>authorize</button>
                </p>
            {/if}
        {/each}
    </div>
    <div>
        <input bind:value={authorize_school_id}>
        <input bind:value={username}>
        <input type="password" bind:value={password}>
        <button on:click={authorize_school}>Authorize School</button>
        <div>
            {authorization_message}
        </div>
    </div>
</main>

<style lang="scss">
</style>

