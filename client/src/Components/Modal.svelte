<script>
    import {active_modal} from '../stores.js';

    export let id;
    let dialog;
    let open = false;

    function scrollbar_visible() {
        return document.documentElement.scrollHeight > document.documentElement.clientHeight;
    }

    function toggle_modal(active_modal) {
        if(active_modal === id) {
            open = true;
            if(scrollbar_visible()) {
                document.documentElement.style.top = `-${window.scrollY}px`;
                document.documentElement.style.position = 'fixed';
            }
            dialog.showModal();
        } else if (open) {
            open = false;
            dialog.close();
            const scrollY = document.documentElement.style.top;
            document.documentElement.style.position = '';
            document.documentElement.style.top = '';
            window.scrollTo(0, parseInt(scrollY || '0') * -1);
        }
    }

    $: dialog && toggle_modal($active_modal);
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
<dialog bind:this={dialog} on:close={() => {$active_modal = ""}} on:click|self={() => {dialog.close()}}>
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
        left: calc(50% + (100vw - 100%) / 2);
        transform: translate(-50%, calc(-50% - 20px));
        margin: 0;
        opacity: 0;
        padding: 0;
        pointer-events: none;
        border: none;
        border-radius: 5px;
        background: var(--background);
        color: var(--text-color);
        overflow-y: hidden;
        max-height: calc((100% - 6px) - 2em);
        max-width: calc(100% - 6px - 2em);
        width: clamp(700px, 60vw, 1400px);
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
    }

    .footer {
        display: flex;
        flex-direction: row;
        justify-content: flex-end;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.2);
    }

</style>