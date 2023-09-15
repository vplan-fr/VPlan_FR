<script>
    import { customFetch } from "./utils";

    let changelog = [];
    function get_changelog() {
        customFetch("/api/v69.420/changelog")
            .then(data => {
                if (Array.isArray(data)) {
                    changelog = data;
                }
            })
            .catch(error => {
                changelog = [];
                console.error(error);
            })
    }

    function read_changelog(number) {
        customFetch("/api/v69.420/changelog", {
            method: "POST",
            body: number
        })
            .then(data => {
                notifications.success("Log als gelesen markiert")
            })
            .catch(error => {
                notifications.danger("Log konnte nicht als gelesen markiert werden")
            })
        changelog = changelog.filter(item => item[0] !== number)
    }

    get_changelog();
</script>

<div class="changelog">
    {#each changelog as cur_log}
        <p>
            {cur_log[1]}
            <button on:click={() => {read_changelog(cur_log[0])}}>Als gelesen markieren</button>
        </p>
    {/each}
</div>

<style lang="scss">

</style>