<script>
    import Dropdown from "./Dropdown.svelte";

    export let data = [];
    export let selected_elem = null;
    export let selected_id = null;
    export let icon_location = null;
    export let grouped = false;

    function update_selected_id() {
        selected_id = selected_elem["id"];
    }

    $: selected_elem && update_selected_id();
</script>

<!-- Preloading Icons -->
<svelte:head>
    {#if icon_location}
        {#each data as elem}
            {#if grouped}
                {#each elem[1] as element}
                    <link rel="preload" as="image" href="{icon_location}/{element["icon"]}" />
                {/each}
            {:else}
                <link rel="preload" as="image" href="{icon_location}/{elem["icon"]}" />
            {/if}
        {/each}
    {/if}
</svelte:head>

<div class="select-wrapper">
    <Dropdown let:toggle small_version={true} transform_origin_x="100%">
        <button type="button" slot="toggle_button" on:click={toggle} class="toggle-btn">
            {#if selected_elem && selected_id}
                {selected_elem["name"]}
            {:else}
                <slot></slot>
            {/if}
            <span class="material-symbols-outlined dropdown-arrow">arrow_drop_down</span>
        </button>

        {#each data as elem}
            {#if grouped}
                <span class="heading">{elem[0]}</span>
                {#each elem[1] as element}
                    <button type="button" class="select-option indented {icon_location ? "" : "no_icons"}" on:click={() => {selected_elem = element}}>
                        {element["name"]}
                        {#if icon_location}
                            <img src="{icon_location}/{element["icon"]}" alt="Schul-Logo" class="school-logo">
                        {/if}
                    </button>
                {/each}
            {:else}
                <button type="button" class="select-option {icon_location ? "" : "no_icons"}" on:click={() => {selected_elem = elem}}>
                    {elem["name"]}
                    {#if icon_location}
                        <img src="{icon_location}/{elem["icon"]}" alt="Schul-Logo" class="school-logo">
                    {/if}
                </button>
            {/if}
        {/each}
    </Dropdown>
</div>

<style lang="scss">
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
        padding: 10px;
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