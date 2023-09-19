<script>
    import { flip } from 'svelte/animate';
    import { fly } from "svelte/transition";
    import {removeNotification} from "../notifications.js";
    import {notifications_list} from "../stores.js";

    export let themes = {
        danger: "#E26D69",
        success: "#84C991",
        warning: "#f0ad4e",
        info: "#5bc0de",
        default: "#aaaaaa",
    };


</script>

<div class="notifications">
    {#each $notifications_list as notification (notification.id)}
    <!-- svelte-ignore a11y-click-events-have-key-events -->    
        <div
            class="toast"
            style="background: {themes[notification.type]};"
            in:fly={{ y: 30 }}
            out:fly={{y: -30}}
            animate:flip={{duration: 500}}
            on:click={() => {removeNotification(notification.id)}}
        >
            <div class="content">{notification.message}</div>
            {#if notification.icon}<i class={notification.icon} />{/if}
        </div>
    {/each}
</div>

<style lang="scss">
    .notifications {
        position: fixed;
        top: 61px;
        @media only screen and (min-width: 602px) {
            top: 69px;
        }
        right: 0;
        margin: 0 auto;
        padding: 5px;
        z-index: 9998;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: flex-end;
    }

    .toast {
        flex: 0 0 auto;
        margin-bottom: 5px;
        pointer-events: all;
    }

    .content {
        padding: 10px;
        display: block;
        color: white;
        pointer-events: none;
        user-select: none;
    }
</style>