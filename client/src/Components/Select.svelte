<script>
    import Dropdown from "./Dropdown.svelte";

    export let data = [];
    export let selected_elem;
    export let icon_location;
    export let height_limit = false;
</script>

<!-- Preloading Icons -->
<svelte:head>
    {#each Object.entries(data) as elem}
        <link rel="preload" as="image" href="{icon_location}/{elem[1]["icon"]}" />
    {/each}
</svelte:head>

<div class="select-wrapper">
    <Dropdown let:toggle small_version={true} transform_origin="100% 0%" height_limit={height_limit}>
        <button  type="button" slot="toggle_button" on:click={toggle} class="toggle-btn">
            {#if selected_elem}
                {data[selected_elem]["name"]}
            {:else}
                <slot></slot>
            {/if}
        </button>
    
        {#each Object.entries(data) as elem}
            <button type="button" class="select-option {icon_location ? "" : "no_icons"}" on:click={() => {selected_elem = elem[0]}}>
                {elem[1]["name"]}
                {#if icon_location}
                    <img src="{icon_location}/{elem[1]["icon"]}" alt="Schul-Logo" class="school-logo">
                {/if}
            </button>
        {/each}
    </Dropdown>
</div>

<style lang="scss">
    .select-wrapper {
        margin-bottom: 10px;
    }

    .toggle-btn {
        width: 100%;
        height: 100%;
        font-size: var(--font-size-base);
        padding: 10px;
        padding-right: 1.5em;
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
    }
</style>