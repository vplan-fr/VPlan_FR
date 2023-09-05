<script>
    import { createEventDispatcher } from "svelte";
    import {notifications} from './notifications.js';

    const dispatch = createEventDispatcher();
    function closePopup() {
        dispatch("close");
    }

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
        fetch("/schools")
            .then(response => response.json())
            .then(data => {
                schools = data;
            })
            .catch(error => {
                notifications.danger("Schulen laden fehlgeschlagen!", 2000);
            })
    }
    function get_authorized_schools() {
        fetch("/authorized_schools")
            .then(response => response.json())
            .then(data => {
                authorized_school_ids = data;
            })
            .catch(error => {
                notifications.danger("Authorisierte Schulen laden fehlgeschlagen!", 2000);
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
        formData.append('school_num', authorize_school_id);
        formData.append('username', username);
        formData.append('pw', password);
        fetch("/authorize", {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if ("error" in data) {
                    authorization_message = data["error"];
                    return
                }
                authorization_message = "Success!!!"
                authorized_school_ids = [...authorized_school_ids, authorize_school_id];
            })
            .catch(error => {
                notifications.danger("Schule Authorisieren fehlgeschlagen!", 2000);
            }
        );
    }
    get_schools();
    get_authorized_schools();
    //$: console.log(schools);
    //$: console.log(authorized_school_ids);
</script>



<div class="popup">
    <div id="authorized_schools">
        {#each authorized_school_ids as school_id}
            <p>{schools[school_id]["name"]}<button on:click={() => {
                school_num = school_id;
                localStorage.setItem('school_num', `${school_num}`)
            }}>Choose</button></p>
        {/each}
    </div>
    <div id="unauthorized_schools">
        {#each Object.keys(schools) as school_id}
            {#if !isObjectInList(school_id, authorized_school_ids)}
                <p>
                    {schools[school_id]["name"]} ({school_id})
                    <button on:click={() => authorize_school_id=school_id}>authorize</button>
                </p>
            {/if}
        {/each}
    </div>
    <div id="authorize_school_wrapper">
        <input bind:value={authorize_school_id}>
        <input bind:value={username}>
        <input type="password" bind:value={password}>
        <button on:click={authorize_school}>Authorize School</button>
        <div id="authorization_messages">
            {authorization_message}
        </div>
    </div>
    <div id="popup_close_wrapper">
        <button on:click={closePopup}>X</button>
    </div>
</div>

<style lang="scss">
    .popup {
        position: fixed;
        top: 5%;
        left: 5%;
        width: 90%;
        height: 90%;
        background-color: rgba(0, 0, 0, 0.98);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        #authorized_schools {

        }
        #unauthorized_schools {

        }
        #authorize_school_wrapper {
            position: absolute;
            bottom: 20px;
            width: 100%;
        }
        #popup_close_wrapper {
            position: absolute;
            top: 0;
            right: 0;
        }
    }
</style>

