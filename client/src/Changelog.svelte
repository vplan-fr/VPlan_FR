<script>
    import { customFetch } from "./utils";
    import {active_modal} from './stores';
    import Modal from "./Components/Modal.svelte";
    import { flip } from "svelte/animate";
    import { fade } from "svelte/transition";

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

<Modal id="changelog">
    <h1 class="responsive-heading">Changelog</h1>
    <div class="changelog">
        {#each changelog as cur_log, index (index)}
        <div class="changelog_entry" animate:flip>
            <span class="changelog_entry_content responsive-text">
                {cur_log[1]}
            </span>
            <button on:click={() => {read_changelog(cur_log[0])}} class="button btn-small mark-read-btn"><span class="material-symbols-outlined">close</span></button>
        </div>
        {:else}
        <span class="responsive-text">Keine neuen Änderungen vorhanden.</span>
        {/each}
    </div>
    <svelte:fragment slot="footer">
        <button class="button btn-small" on:click={() => {$active_modal = ""}}>Schließen</button>
    </svelte:fragment>
</Modal>


<style lang="scss">
    .changelog {
        display: grid;
        gap: 10px;
        justify-content: start;

        .changelog_entry {
            display: flex;
            align-items: center;
            flex-direction: row;
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            padding: 10px;
            border-radius: 5px;

            .changelog_entry_content {
                flex: 1;
            }

            .mark-read-btn {
                display: inline-flex !important;
                aspect-ratio: 1;

                span {
                    margin-left: 0 !important;
                    font-weight: 600;
                }
            }
        }
    }

    .button {
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        border: none;
        background-color: rgba(255, 255, 255, 0.2);
        color: var(--text-color);
        border-radius: 5px;
        padding: .5em;
        margin: 3px;
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
</style>