<script>
    import { scale } from "svelte/transition";

    export let transitionFunction = scale;
    export let transitionOptions = {duration: 200, start: 0.3};
    export let transform_origin = "100% 0%";
    export let small_version = false;
    let open = false;

    function clickOutside(node, { enabled: initialEnabled, cb }) {
        const handleOutsideClick = ({ target }) => {
            if (!node.contains(target)) {
                cb();
            }
        };

        function update({enabled}) {
            if (enabled) {
                window.addEventListener('click', handleOutsideClick);
            } else {
                window.removeEventListener('click', handleOutsideClick);
            }
        }

        update({ enabled: initialEnabled });
        return {
            update,
            destroy() {
                window.removeEventListener( 'click', handleOutsideClick );
            }
        };
    }
</script>

<div class="dropdown-wrapper {small_version ? "small_version": ""} {open ? "open": ""}">
    <div class="btn-wrapper" use:clickOutside={{ enabled: open, cb: () => open = false }}>
        <slot name="toggle_button" toggle={() => {open = !open}} />
    </div>
    {#if open}
        <div class="dropdown-content" transition:transitionFunction="{transitionOptions}" style="transform-origin: {transform_origin};">
            <slot />
        </div>
    {/if}
</div>

<style lang="scss">
    .dropdown-wrapper {
        position: relative;
        width: 100%;
        height: 100%;

        .btn-wrapper {
            width: 100%;
            height: 100%;
        }

        .dropdown-content {
            position: absolute;
            bottom: 0;
            right: 0;
            transform: translateY(100%);
            z-index: 999;

            display: flex;
            flex-direction: column;
            width: max-content;
            
            background: var(--background-color);
            box-shadow: 0px 0px 6px rgba(0, 0, 0, 0.3);

            &::before {
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.07);
                pointer-events: none;
            }
        }

        &.small_version {
            .dropdown-content {
                box-shadow: 0 4px 4px -1px rgba(0, 0, 0, 0.2), 0 5px 5px 0 rgba(0, 0, 0, 0.14), 0 10px 10px 0 rgba(0, 0, 0, 0.12);
                min-width: 100%;
                border-radius: 5px;
                overflow: hidden;
            }
        }
    }
</style>