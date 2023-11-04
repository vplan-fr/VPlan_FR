<script>
    import { onMount } from "svelte";
    import Dropdown from "./Dropdown.svelte";

    export let data = [];
    export let selected_elem = null;
    export let selected_id = null;
    export let icon_location = null;
    export let grouped = false;
    export let data_name = "Elemente";
    export let preselect = null;
    export let onchange = () => {};
    let toggle_button;
    let selected_index = (preselect !== null) ? preselect : null;
    let grouped_length = null;

    function keydown_handler(event) {
        if(event.key === "ArrowDown") {
            event.preventDefault();
            if(selected_index === null) {
                selected_index = 0;
                return;
            }
            change_index(1);
        } else if(event.key === "ArrowUp") {
            event.preventDefault();
            if(selected_index === null) {
                if(grouped) {
                    selected_index = grouped_length-1;
                } else {
                    selected_index = data.length-1;
                }
                return;
            }
            change_index(-1);
        }
    }

    onMount(() => {
        toggle_button.addEventListener("keydown", keydown_handler);
    });

    function calc_grouped_length(data) {
        let curr_length = 0;
        for(let elem of data) {
            curr_length += elem[1].length;
        }
        grouped_length = curr_length;
    }

    function change_index(direction) {
        let tmp_result = selected_index + direction;
        if(grouped) {
            if((tmp_result < 0) || (tmp_result > (grouped_length-1))) {return;}
        } else {
            if((tmp_result < 0) || (tmp_result > (data.length-1))) {return;}
        }
        selected_index = tmp_result;
    }

    function get_by_oned_index(index) {
        let tmp_indices_remaining = index;
        for(let i = 0; i < data.length; i++) {
            if(data[i][1].length <= tmp_indices_remaining) {
                tmp_indices_remaining -= data[i][1].length;
            } else {
                return [i, tmp_indices_remaining];
            }
        }
    }

    function turn_to_oned_index(index1, index2) {
        let curr_index = 0;
        for(let i = 0; i < index1; i++) {
            curr_index += data[i][1].length;
        }
        curr_index += index2
        return curr_index;
    }

    function update_selected() {
        if (grouped) {
            let twod_index = get_by_oned_index(selected_index);
            selected_elem = data[twod_index[0]][1][twod_index[1]];
        } else {
            selected_elem = data[selected_index];
        }
        selected_id = selected_elem.id;
        onchange();
    }

    function unselect() {
        selected_index = null;
        selected_elem = null;
    }

    $: (selected_id === null) && unselect();
    $: grouped && calc_grouped_length(data);
    $: (selected_index !== null) && update_selected();
</script>

<!-- Preloading Icons -->
<svelte:head>
    {#if icon_location}
        {#each data as elem}
            {#if grouped}
                {#each elem[1] as element}
                    {#if element.icon}
                        <link rel="preload" as="image" href="{icon_location}/{element.icon}" />
                    {/if}
                {/each}
            {:else}
                {#if elem.icon}
                    <link rel="preload" as="image" href="{icon_location}/{elem.icon}" />
                {/if}
            {/if}
        {/each}
    {/if}
</svelte:head>

<div class="select-wrapper">
    <Dropdown let:toggle small={true} transform_origin_x="100%">
        <button bind:this={toggle_button} type="button" slot="toggle_button" on:click={toggle} class="toggle-btn">
            {#if selected_elem}
                {selected_elem.display_name}
            {/if}
            <div class="label" class:small={selected_elem}>
                <slot></slot>
            </div>
            <span class="material-symbols-outlined dropdown-arrow">arrow_drop_down</span>
        </button>

        {#each data as elem, index1}
            {#if grouped}
                <span class="heading">{elem[0]}</span>
                {#each elem[1] as element, index2}
                    <button type="button" class="select-option indented" class:no_icons={!icon_location} on:click={() => {selected_index = turn_to_oned_index(index1, index2); toggle_button.focus();}}>
                        {element.display_name}
                        {#if icon_location && element.icon}
                            <img src="{icon_location}/{element.icon}" alt="Schul-Logo" class="school-logo">
                        {/if}
                    </button>
                {:else}
                    <span class="no-options-placeholder">
                        Keine {data_name} vorhanden
                    </span>
                {/each}
            {:else}
                <button type="button" class="select-option" class:no_icons={!icon_location} on:click={() => {selected_index = index1; toggle_button.focus();}}>
                    {elem.display_name}
                    {#if icon_location && elem.icon}
                        <img src="{icon_location}/{elem.icon}" alt="Schul-Logo" class="school-logo">
                    {/if}
                </button>
            {/if}
        {:else}
            <span class="no-options-placeholder">
                Keine {data_name} vorhanden
            </span>
        {/each}
    </Dropdown>
</div>

<style lang="scss">
    .label {
        transition: all .2s ease;
        &.small {
            position: absolute;
            top: 0;
            left: 0;
            font-size: 0.8em;
            filter: brightness(0.5);
            transform: translateY(-25%);
        }
    }

    .no-options-placeholder {
        padding: 15px;
        display: block;
    }

    .heading {
        display: block;
        font-weight: 700;
        padding: 15px;
        font-size: var(--font-size-md);
    }

    .dropdown-arrow {
        display: block;
        transition: transform .2s ease;
        pointer-events: none;
        font-size: var(--font-size-lg);
        margin-left: .3em;
    }

    :global(.open) .dropdown-arrow {
        transform: rotate(180deg);
    }

    .select-wrapper {
        margin-bottom: 10px;
    }

    .toggle-btn {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        height: 100%;
        font-size: var(--font-size-base);
        padding: 15px 10px 5px 10px;
        text-align: left;
        border: none;
        border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        background-color: transparent;
        color: var(--text-color);
    }
    .select-option {
        width: 100%;
        display: flex;
        flex-direction: row;
        align-items: center;
        text-align: left;
        justify-content: space-between;
        font-size: var(--font-size-base);
        padding: 5px 10px;
        border: none;
        background-color: transparent;
        color: var(--text-color);
        transition: background-color .2s ease;

        &.no_icons {
            padding: 15px 20px;
        }

        &:hover, &:focus-visible {
            background-color: rgba(0, 0, 0, 0.3);
        }

        .school-logo {
            height: 40px;
            margin: 5px;
            border-radius: 5px;
            aspect-ratio: 1;
            object-fit: contain;
        }

        &.indented {
            padding-left: 40px;
        }
    }
</style>