<script>
    import { createEventDispatcher } from "svelte";
    const dispatch = createEventDispatcher();
    function closePopup() {
        dispatch("close");
    }
    let schools = {};
    let authorized_school_ids = [];
    function get_schools() {
        fetch("/schools")
            .then(response => response.json())
            .then(data => {
                schools = data;
            })
            .catch(error => {
                console.error(error);
            })
    }
    function get_authorized_schools() {
        fetch("/authorized_schools")
            .then(response => response.json())
            .then(data => {
                authorized_school_ids = data;
            })
            .catch(error => {
                console.error(error);
            }
        );
    }
    function authorize_school() {
        get_authorized_schools();
    }
    get_schools();
    get_authorized_schools();
    console.log(schools);
    console.log(authorized_school_ids);
</script>



<div class="popup">
    <p>This is the pop-up content.</p>
    {#each authorized_school_ids as school}
        <p>{schools[school] || ""}</p><br>
    {/each}
    {#each schools as school}
        <p>school</p>
    {/each}
    <button on:click={closePopup}>Close</button>
</div>

<style>
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
    }
</style>

