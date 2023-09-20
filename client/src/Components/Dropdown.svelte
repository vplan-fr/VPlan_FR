<script>
    import { scale } from "svelte/transition";

    export let transitionFunction = scale;
    export let transitionOptions = {duration: 200, start: 0.3};
    export let transform_origin_x = "100%";
    export let small_version = false;
    export let flipped = false;
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

<div class="dropdown-wrapper" class:small_version class:open>
    <div class="btn-wrapper" use:clickOutside={{ enabled: open, cb: () => open = false }}>
        <slot name="toggle_button" toggle={() => {open = !open}} />
    </div>
    {#if open}
        <div class="dropdown-content" transition:transitionFunction="{transitionOptions}" style="--transform-origin-x: {transform_origin_x}" class:flipped_top={flipped}>
            <div class="height-limiter">
                <slot />
            </div>
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
            transform-origin: var(--transform-origin-x) 0%;

            display: flex;
            flex-direction: column;
            width: max-content;
            
            background: var(--background);
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

            .height-limiter {
                max-height: min(350px, 50vh);
                overflow-y: auto;

                @media only screen and (min-width: 1501px) {
                    max-height: min(500px, 50vh);
                }
            }
        }

        &.small_version {
            .dropdown-content {
                bottom: -10px;
                box-shadow: 0 4px 4px -1px rgba(0, 0, 0, 0.2), 0 5px 5px 0 rgba(0, 0, 0, 0.14), 0 10px 10px 0 rgba(0, 0, 0, 0.12);
                width: 100%;
                border-radius: 5px;
                @media only screen and (min-width: 1501px) {
                    border-radius: 8px;
                }
                overflow: hidden;

                &.flipped_top {
                    top: 0px;
                    border-radius: 0px;
                    width: fit-content;
                    bottom: unset;
                    transform: translateY(-100%);
                    transform-origin: var(--transform-origin-x) 100%;
                }
            }
        }
    }
</style>