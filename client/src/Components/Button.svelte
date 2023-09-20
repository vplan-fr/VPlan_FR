<script>
    export let background = "rgba(255, 255, 255, 0.2)";
    export let small = false;
    export let type = "button";
</script>

<button on:click class={$$props.class} id={$$props.id} class:small style="background: {background}" type={type}>
    <slot>Button</slot>
</button>

<style lang="scss">
    button {
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        border: none;
        color: var(--text-color);
        border-radius: 5px;
        padding: .5em;
        margin: 3px;
        font-size: var(--font-size-base);
        position: relative;

        .material-symbols-outlined {
            font-size: 1.3em;
            float: right;
            margin-left: .2em;
        }

        &.small {
            font-size: var(--font-size-sm);
        }
    }
</style>