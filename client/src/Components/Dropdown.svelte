<script>
    import { scale } from "svelte/transition";

    export let transitionFunction = scale;
    export let transitionOptions = {duration: 200, start: 0.3};
    export let transform_origin = "100% 0%";
    export let small_version = false;
    export let arrow_visible = true;
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

<div class="dropdown-wrapper {small_version ? "small_version": ""} {open ? "open": ""} {arrow_visible ? "arrow_visible" : ""}">
    <div class="btn-wrapper" use:clickOutside={{ enabled: open, cb: () => open = false }}>
        <slot name="toggle_button" toggle={() => {open = !open}} />
        <span class="material-symbols-outlined dropdown-arrow">arrow_drop_down</span>
    </div>
    {#if open}
        <div class="dropdown-content" transition:transitionFunction="{transitionOptions}" style="transform-origin: {transform_origin};">
            <div class="height-limiter">
                <slot />
            </div>
        </div>
    {/if}
</div>

<style lang="scss">
    .dropdown-arrow {
        display: none;
    }

    .arrow_visible {
        .btn-wrapper {
            padding-right: .9em;

            @media only screen and (min-width: 1501px) {
                padding-right: 1.5em;
            }
        }

        .dropdown-arrow {
            display: block;
            position: absolute;
            top: 50%;
            right: 0;
            transform: translateY(-50%);
            transition: transform .2s ease;
            pointer-events: none;
            font-size: 1.5em;

            @media only screen and (min-width: 1501px) {
                font-size: 2em;
            }
        }

        &.open {
            .dropdown-arrow {
                transform: rotate(180deg) translateY(50%);
            }
        } 
    }

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

            .height-limiter {
                max-height: min(500px, 50vh);
                overflow-y: scroll;
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
            }
        }
    }
</style>