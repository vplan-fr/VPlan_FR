<script>
    import CollapsibleWrapper from "./Components/CollapsibleWrapper.svelte";
    import {group_rooms} from "./utils.js";
    import Collapsible from "./Components/Collapsible.svelte";
    import { fade } from "svelte/transition";

    export let rooms_data;
    export let all_rooms;
    export let plan_type;
    export let plan_value;
    export let extra_height = true;
    let used_rooms_hidden = true;

    $: all_rooms_grouped = all_rooms ? group_rooms(all_rooms) : []
    $: all_rooms_grouped_dict = Object.fromEntries(all_rooms_grouped)
</script>

<div class:extra-height={extra_height}>
    <h1 class="responsive-heading">Freie Räume</h1>
    {#if rooms_data?.free_rooms_by_block == null}
        <h1>Nicht verfügbar.</h1>
    {:else}
        <CollapsibleWrapper let:closeOtherPanels>
            {#each Object.entries(rooms_data.free_rooms_by_block) as [block, free_rooms], i}
                <Collapsible on:panel-open={closeOtherPanels} let:toggle>
                    <button slot="handle" on:click={toggle} class="toggle-button" class:first={i == 0} class:last={i == Object.entries(rooms_data.free_rooms_by_block).length-1}>{block}. Block</button>
                    <div class="block">
                        <ul>
                            {#each group_rooms(Object.fromEntries(free_rooms.map(r => [r, all_rooms[r]]))) as [category, rooms]}
                                <li>{category}:<br><br>
                                    {#each rooms as room}
                                        <button class="chip info-element" on:click={() => {
                                            plan_type = 'rooms';
                                            plan_value = room;
                                        }}>
                                            <span>{room}</span>
                                        </button>
                                    {/each}
                                    {#if !used_rooms_hidden}
                                        {#each all_rooms_grouped_dict[category].filter(n => !rooms.includes(n)) as room}
                                            <button class="chip info-element used-room" on:click={() => {
                                                plan_type = 'rooms';
                                                plan_value = room;
                                            }} transition:fade={{duration: 200}}>
                                                <span>{room}</span>
                                            </button>
                                        {/each}
                                    {/if}
                                </li>
                            {/each}
                        </ul>
                    </div>
                </Collapsible>
            {/each}
        </CollapsibleWrapper>
    {/if}
    <button on:click={() => {used_rooms_hidden = !used_rooms_hidden}} class="plus-btn">+</button>
</div>

<style lang="scss">
    .plus-btn {
        position: absolute;
        top: 0;
        right: 0;
        border: none;
        font-size: clamp(1.063rem, 4vw, 2.28rem);
        height: clamp(1.063rem, 4vw, 2.28rem);
        aspect-ratio: 1;
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.08);
        color: var(--text-color);
        display: flex;
        justify-content: center;
        align-items: center;
        transition: background-color .2s ease;

        &:hover, &:focus-visible {
            background-color: rgba(255, 255, 255, 0.05);
        }
    }

    ul {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .extra-height {
        position: relative;
        min-height: calc(100vh - 56px);

        @media only screen and (min-width: 1501px) {
            min-height: calc(100vh - 64px);
        }
    }
    
    .toggle-button {
        font-size: clamp(1.063rem, 1.5vw, 1.28rem);
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

    .responsive-heading {
        font-size: clamp(1.063rem, 4vw, 2.28rem);
        line-height: 1.6;
        margin-bottom: 15px;
    }

    .block {
        padding: 20px 0px;
    }

    .chip {
        display: inline-block;
        vertical-align: middle;
        padding: 0.5em 1.7em;
        margin: .4em;
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