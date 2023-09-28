<script>
    /**
     * @slot {{ toggle: () => void }} handle
     * @event {{ close: () => void; toggle: () => void }} panel-open
     * @event {{ close: () => void; toggle: () => void }} panel-close
     */
    import { createEventDispatcher } from 'svelte';
    import { slide } from 'svelte/transition';
    function classes(...args) {
        return args.filter(cls => !!cls).join(' ');
    }
  
    let _class = null;
    /** @type {string | false | null} */
    export { _class as class };
  
    /**
     * The state of the section: opened or closed.
     * @type {boolean}
     */
    export let open = false;
  
    const selfControl = {
      close() {
        open = false;
      },
      toggle() {
        dispatch(!open ? 'panel-open' : 'panel-close', selfControl);
        open = !open;
      },
    };
  
    const dispatch = createEventDispatcher();
</script>

<li class:open class={classes('panel', _class)}>
    <slot name="handle" toggle={selfControl.toggle}></slot>
</li>
{#if open}
<section transition:slide|local>
    <slot />
</section>
{/if}

<style lang="scss">

</style>