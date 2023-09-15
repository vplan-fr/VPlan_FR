<script>
    export let showModal;
    let dialog;

    $: dialog && (showModal ? dialog.showModal() : dialog.close());
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
<dialog bind:this={dialog} on:click|self={() => {showModal = false}}>
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div on:click|stopPropagation class="content-scroll">
        <slot />
    </div>
    <div class="footer">
        <slot name="footer" />
    </div>
</dialog>

<style lang="scss">
    dialog {
        transition: all .3s ease;
        display: flex;
        flex-direction: column;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, calc(-50% - 20px));
        margin: 0;
        opacity: 0;
        padding: 0;
        pointer-events: none;
        border: none;
        max-width: 32em;
        border-radius: 5px;
        background: var(--background);
        color: var(--text-color);
        overflow-y: hidden;
        max-height: calc((100% - 6px) - 2em);
        max-width: 60%;
        z-index: 9999;

        .content-scroll {
            overflow-y: auto;
            padding: 20px;
            max-height: calc((100% - 46px) - 2em);
            flex: 1;
        }

        &::before {
            content: "";
            position: absolute;
            inset: 0;
            background-color: rgba(255, 255, 255, 0.08);
            z-index: -1;
            pointer-events: none;
        }
    }
    
    dialog[open] {
        transform: translate(-50%, -50%);
        opacity: 1;
        pointer-events: all;
    }
    
    dialog::backdrop {
        background-color: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(3px);
    }

    .footer {
        display: flex;
        flex-direction: row;
        justify-content: flex-end;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
    }

</style>