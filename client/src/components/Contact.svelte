<script>
    import {customFetch, navigate_page} from "../utils.js";
    import {notifications} from "../notifications.js";
    import Select from "../base_components/Select.svelte";
    import { onMount } from "svelte";
    import { title } from "../stores.js";
    import Button from "../base_components/Button.svelte";

    let category = "bug";
    let person = "student";
    let contact_data = "";
    let message = "";

    function send_message() {
        customFetch("/api/v69.420/contact", {
            method: "POST",
            body: JSON.stringify({
                "category": category,
                "person": person,
                "contact_data": contact_data,
                "message": message
            })
        })
            .then(data => {
                notifications.success("Nachricht übermittelt");
                navigate_page("plan");
            })
            .catch(error => {
                notifications.danger(error.message);
            })
    }

    onMount(() => {
        location.hash = "#contact";
        title.set("Kontaktformular");
        // console.log("Mounted Contact.svelte");
    });
</script>

<div>
    <h1 class="responsive-heading">Kontaktiere uns</h1>
    <div class="horizontal-align">
        <Select data={[
            {"id": "bug", "display_name": "Bug"},
            {"id": "enhancement", "display_name": "Feature-Request"},
            {"id": "authorization", "display_name": "Schulautorisierung"},
            {"id": "advertisement", "display_name": "Werbung"},
            {"id": "sponsoring", "display_name": "Sponsoren"},
            {"id": "questions", "display_name": "Fragen zur Website"},
            {"id": "else", "display_name": "Sonstiges"},
        ]} bind:selected_id={category} preselect={0}>Nachrichtenkategorie</Select>
        <Select data={[
            {"id": "student", "display_name": "Schüler"},
            {"id": "teacher", "display_name": "Lehrer"},
            {"id": "head_teacher", "display_name": "Schulleiter"},
            {"id": "developer", "display_name": "Developer"},
            {"id": "else", "display_name": "Sonstige"}
        ]} bind:selected_id={person} preselect={0}>Absender</Select>
    </div>
    
    <label for="contact_data">Deine Kontaktdaten (Discord/E-Mail/Telefon):</label>
    <input class="textfield" name="contact_data" type="text" bind:value={contact_data}>
    <label for="message">Deine Nachricht:</label>
    <textarea class="textfield" name="message" bind:value={message} style="resize: vertical; max-height: 500px" maxlength="1024"></textarea>
    <Button background="var(--accent-color)" on:click={send_message}>Absenden</Button>
</div>

<style lang="scss">
    .horizontal-align {
        display: flex;
        flex-direction: row;
        gap: 15px;
        margin-bottom: 20px;

        :global(.select-wrapper) {
            flex: 1;
        }
    }

    label {
        display: block;
        margin-top: 4px;
        margin-bottom: 8px;
        font-size: var(--font-size-base);
    }

    .textfield {
        width: 100%;
        padding: 12px 20px;
        margin-bottom: 8px;
        box-sizing: border-box;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background-color: rgba(255, 255, 255, 0.1);
        color: var(--text-color);
        border-radius: 5px;
    }
</style>