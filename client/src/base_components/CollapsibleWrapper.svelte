<script>
    /**
     * @typedef {{ close: () => void; toggle: () => void }} AccordionSectionControl
     * @slot {{ closeOtherPanels: (e: CustomEvent<AccordionSectionControl>) => void }}
     */
    function classes(...args) {
        return args.filter(cls => !!cls).join(' ');
    }
  
    let _class = null;
    /** @type {string | false | null} */
    export { _class as class };
    /**
     * Setting this to true allows multiple panels to be open at the same time.
     * @type {boolean}
     */
    export let multiple = false;
  
    /**
     * @type {AccordionSectionControl | null}
     */
    let currentlyOpenPanel = null;
  
    function closeOtherPanels({ detail: thisPanel }) {
      if (
        currentlyOpenPanel != null &&
        currentlyOpenPanel !== thisPanel &&
        !multiple
      ) {
        currentlyOpenPanel.close();
      }
      currentlyOpenPanel = thisPanel;
    }
</script>

<ul class={classes('accordion', _class)} {...$$restProps}>
    <slot {closeOtherPanels} />
</ul>

<style lang="scss">
    ul {
        padding-left: 0 !important;
        @media only screen and (max-width: 1501px) {
            padding-left: 0px !important;
        }
        list-style-type: none !important;
    }
    .accordion {
        overflow: hidden;
        border-radius: 5px;

        @media only screen and (min-width: 1501px) {
            border-radius: 8px;
        }
    }
</style>