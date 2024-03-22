<script>
    import {active_modal, inspecting_day} from "../../stores.js";
    import Modal from "../../base_components/Modal.svelte";
    import Button from "../../base_components/Button.svelte";
    import DayInfos from "../Plan/DayInfos.svelte";
</script>

<Modal id="day-inspect">
    <h1 class="responsive-heading">{$inspecting_day ? $inspecting_day.date : "..."}</h1>

    {#if $inspecting_day}
        <DayInfos
            exams={$inspecting_day.exams}
            info={$inspecting_day.info}
            revision_arr={[]}
            is_default_plan={$inspecting_day.is_default_plan}
            last_fetch={$inspecting_day.last_fetch}
            selected_revision={null}
            date={null}
            plan_type={null}
            plan_value={null}
            text_color="white"
        />
    {/if}

    <svelte:fragment slot="footer">
        <Button on:click={() => {$active_modal = ""}} small={true}>Schließen</Button>
    </svelte:fragment>
</Modal>