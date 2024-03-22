<script>
    import {active_modal, inspecting_lesson} from "../../stores.js";
    import Modal from "../../base_components/Modal.svelte";
    import Button from "../../base_components/Button.svelte";
    import Lesson from "../Plan/Lesson.svelte";
</script>

<Modal id="lesson-inspect">
    <h1 class="responsive-heading">Stundeninspektor</h1>

    {#if $inspecting_lesson}
        <Lesson
            lesson={$inspecting_lesson}
            plan_type={null}
            plan_value={null}
            date={null}
            display_time={true}
            disable_interactions={true}
        />
    {/if}

    <svelte:fragment slot="footer">
        <Button on:click={() => {$active_modal = ""}} small={true}>Schließen</Button>
    </svelte:fragment>
</Modal>