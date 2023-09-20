<script>
    import { customFetch } from "./utils";
    import {active_modal, logged_in} from './stores';
    import { notifications } from "./notifications";
    import Modal from "./Components/Modal.svelte";
    import SvelteMarkdown from 'svelte-markdown'
    import { onMount } from "svelte";

    let changelog = [];
    function get_changelog() {
        customFetch("/api/v69.420/changelog")
            .then(data => {
                if (Array.isArray(data)) {
                    changelog = data;
                }
            })
            .catch(error => {
                console.error("Changelog konnte nicht geladen werden.");
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

    // onMount(() => {
    //     console.log("Mounted Changelog.svelte");
    // });

    $: $logged_in && get_changelog();
</script>

<Modal id="changelog">
    <h1 class="responsive-heading">Changelog</h1>
    <div class="changelog">
        <span>Ungelesen:</span>
        {#each changelog.reverse().filter(cur_changelog => cur_changelog[1] === false) as changelog_entry, index (index)}
        <div class="changelog_entry">
            <div class="changelog_entry_content">
                <header>
                    <div>
                        <span class="title">{changelog_entry[2]["title"]}</span>
                        <span class="version custom-badge">{changelog_entry[2]["version"]}</span>
                    </div>
                    <button on:click={() => {read_changelog(changelog_entry[0])}} class="button btn-small mark-read-btn"><span class="material-symbols-outlined">close</span></button>
                </header>
                <div class="content">
                    <SvelteMarkdown source={changelog_entry[2]["content"]} />
                </div>
                <span class="date">{changelog_entry[2]["date"]}</span>
            </div>
        </div>
        {:else}
        <span class="responsive-text">Keine neuen Änderungen vorhanden.</span>
        {/each}
        <span>Gelesen:</span>
        {#each changelog.reverse().filter(cur_changelog => cur_changelog[1] === true) as changelog_entry, index (index)}
            <div class="changelog_entry">
                <div class="changelog_entry_content">
                    <header>
                        <div>
                            <span class="title">{changelog_entry[2]["title"]}</span>
                            <span class="version custom-badge">{changelog_entry[2]["version"]}</span>
                        </div>
                    </header>
                    <div class="content">
                        <SvelteMarkdown source={changelog_entry[2]["content"]} />
                    </div>
                    <span class="date">{changelog_entry[2]["date"]}</span>
                </div>
            </div>
        {/each}
    </div>
    <svelte:fragment slot="footer">
        <button class="button btn-small" on:click={() => {$active_modal = ""}}>Schließen</button>
    </svelte:fragment>
</Modal>

<style lang="scss">
    .custom-badge {
        background: rgba(255, 255, 255, 0.07);
        padding: 2px 7px;
        border-radius: 5px;
        white-space: nowrap;
    }

    .changelog {
        display: grid;
        gap: 10px;
        justify-content: start;

        .changelog_entry {
            background: rgba(255, 255, 255, 0.05);
            padding: 10px;
            border-radius: 5px;

            .changelog_entry_content {
                flex: 1;

                header {
                    display: flex;
                    justify-content: space-between;

                    div {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    }
                    margin-bottom: 10px;

                    .title {
                        font-size: var(--font-size-lg);
                        font-weight: 500;
                    }
                }

                .content {
                    font-size: var(--font-size-base);
                    line-height: normal;
                    margin-bottom: 10px;

                    :global(blockquote) {
                        background-color: rgba(255, 255, 255, 0.05);
                        border-left: 4px solid rgba(255, 255, 255, 0.2);
                        padding-left: 10px;
                        border-radius: 0px 5px 5px 0px;
                    }

                    :global(hr) {
                        border-radius: 5px;
                        border: 1px solid rgba(255, 255, 255, 0.3);
                    }

                    :global(ol) {
                        list-style: auto !important;
                    }

                    :global(a) {
                        color: var(--accent-color);
                    }

                    :global(img) {
                        width: 40%;
                        margin: 10px 0;
                    }
                    
                    :global(img[alt=center]) {
                        margin: 10px auto;
                        display: block;
                    }

                    :global(h1) {
                        font-size: var(--font-size-md);
                        font-weight: 600;
                        margin-top: 15px;
                    }

                    :global(strong) {
                        font-weight: 700;
                    }

                    :global(em) {
                        font-style: italic;
                    }

                    :global(del) {
                        text-decoration-thickness: 2px;
                    }

                    :global(code) {
                        background: rgba(0, 0, 0, 0.3);
                        border-radius: 5px;
                        padding: .25em;
                        line-height: 2.2;
                        font-family: "Courier New" !important;
                    }
                    
                    :global(pre) {
                        position: relative;
                        background: rgba(0, 0, 0, 0.3);
                        border-radius: 5px;
                        padding: .5em 1em;
                        margin-bottom: .5em;

                        &::after {
                            content: attr(class);
                            position: absolute;
                            top: 0.5em;
                            right: .7em;
                            font-size: var(--font-size-sm);
                            font-weight: 600;
                        }
                    }

                    :global(pre code) {
                        background: transparent;
                        line-height: normal;
                        padding: 0;
                    }

                    :global(thead) {
                        font-weight: 700;
                        border-bottom: 2px solid var(--text-color);
                    }

                    :global(th) {
                        padding: 0px 10px;
                    }
                }

                .version, .date {
                    font-size: var(--font-size-base);
                }
            }

            .mark-read-btn {
                display: inline-flex !important;
                margin-left: 10px;
                aspect-ratio: 1;
                flex-shrink: 0;
                height: min-content;

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