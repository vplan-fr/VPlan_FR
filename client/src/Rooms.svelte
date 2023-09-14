<script>
    import CollapsibleWrapper from "./Components/CollapsibleWrapper.svelte";
    import {group_rooms} from "./utils.js";
    import Collapsible from "./Components/Collapsible.svelte";
    import { fade } from "svelte/transition";
    import { flip } from "svelte/animate";

    export let rooms_data;
    export let all_rooms;
    export let plan_type;
    export let plan_value;
    export let used_rooms_hidden = true;

    $: all_rooms_grouped = all_rooms ? group_rooms(all_rooms) : []
    $: all_rooms_grouped_dict = Object.fromEntries(all_rooms_grouped)
</script>

{#if rooms_data?.free_rooms_by_block == null}
    <h1 class="responsive-heading">Raumdaten nicht verfügbar.</h1>
{:else}
    <CollapsibleWrapper let:closeOtherPanels>
        {#each Object.entries(rooms_data.free_rooms_by_block) as [block, all_free_rooms], i}
            <Collapsible on:panel-open={closeOtherPanels} let:toggle>
                <button slot="handle" on:click={toggle} class="toggle-button" class:first={i == 0} class:last={i == Object.entries(rooms_data.free_rooms_by_block).length-1}>{block}. Block</button>
                <div class="block">
                    <ul>
                        {#each group_rooms(Object.fromEntries(all_free_rooms.map(r => [r, all_rooms[r]]))) as [category, free_rooms] (category)}
                            <li>{category}:<br><br>
                                {#each all_rooms_grouped_dict[category] as room (room)}
                                    <div animate:flip|local={{duration: 200}} style={(!free_rooms.includes(room) && !used_rooms_hidden) || free_rooms.includes(room) ? "display: inline-block;": "display: none;"}}>
                                        {#if !free_rooms.includes(room) && !used_rooms_hidden}
                                            <button class="chip info-element used-room" on:click={() => {
                                                plan_type = 'rooms';
                                                plan_value = room;
                                            }} transition:fade|local={{duration: 200}}>
                                                <span>{room}</span>
                                            </button>
                                        {:else if free_rooms.includes(room)}
                                            <button class="chip info-element" on:click={() => {
                                                plan_type = 'rooms';
                                                plan_value = room;
                                            }}>
                                                <span>{room}</span>
                                            </button>
                                        {/if}
                                    </div>
                                {/each}
                            </li>
                        {/each}
                    </ul>
                </div>
            </Collapsible>
        {/each}
    </CollapsibleWrapper>
{/if}

<style lang="scss">
    ul {
        display: flex;
        flex-direction: column;
        gap: 20px;
        font-size: var(--font-size-base);
    }

    .extra-height {
        position: relative;
        min-height: calc(100vh - 56px);

        @media only screen and (min-width: 1501px) {
            min-height: calc(100vh - 64px);
        }
    }

    .toggle-button {
        font-size: var(--font-size-base);
        width: 100%;
        border: none;
        padding: .7em;
        background-color: rgba(255, 255, 255, 0.05);
        color: var(--text-color);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        transition: background-color .2s ease;

        &.first {
            border-top: unset;
        }

        &.last {
            border-bottom: unset;
        }

        &:hover, &:focus-visible {
            background-color: rgba(255, 255, 255, 0.03);
        }
    }

    .block {
        padding: 20px 0px;
    }

    .chip {
        font-size: var(--font-size-base);
        display: inline-block;
        vertical-align: middle;
        padding: 0.3em 1.1em;
        margin: .2em;
        border-radius: 999vw;
        border: none;
        background-color: rgba(255, 255, 255, 0.2);
        transition: background-color .2s ease;

        span {
            color: var(--text-color);
            vertical-align: middle;
        }

        &.used-room {
            outline: 2px solid var(--cancelled-color);
            outline-offset: -2px;
        }

        &:hover, &:focus-visible {
            background-color: rgba(255, 255, 255, 0.1);
        }
    }
</style>