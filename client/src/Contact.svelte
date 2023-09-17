<script>
    import {customFetch, navigate_page} from "./utils.js";
    import {notifications} from "./notifications.js";
    import Select from "./Components/Select.svelte";

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
                notifications.danger(error);
            })
    }


</script>

<h1 class="responsive-heading">Kontaktiere uns</h1>
<Select data={[
    {"id": "bug", "name": "Bug"},
    {"id": "enhancement", "name": "Feature-Request"},
    {"id": "authorization", "name": "Schulautorisierung"},
    {"id": "advertisement", "name": "Werbung"},
    {"id": "sponsoring", "name": "Sponsoren"},
    {"id": "questions", "name": "Fragen zur Website"},
    {"id": "else", "name": "Sonstiges"},
]} bind:selected_id={category}>Nachrichtenkategorie</Select>
<Select data={[
    {"id": "student", "name": "Schüler"},
    {"id": "teacher", "name": "Lehrer"},
    {"id": "head_teacher", "name": "Schulleiter"},
    {"id": "developer", "name": "Developer"},
    {"id": "else", "name": "Sonstige"}
]} bind:selected_id={person}>Absender</Select>

<label for="contact_data">Deine Kontaktdaten (Discord/E-Mail/Telefon):</label>
<input class="textfield" name="contact_data" type="text" bind:value={contact_data}>
<label for="message">Deine Nachricht:</label>
<textarea class="textfield" name="message" bind:value={message} style="resize: vertical;"></textarea>
<button class="button" on:click={send_message}>Absenden</button>

<style lang="scss">
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

    .button {
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        border: none;
        background-color: rgba(255, 255, 255, 0.2);
        color: var(--text-color);
        border-radius: 5px;
        padding: .5em;
        margin: 3px;
        font-size: var(--font-size-base);
        position: relative;

        &.btn-small {
            font-size: var(--font-size-sm);
        }

        .material-symbols-outlined {
            font-size: 1.3em;
            float: right;
            margin-left: .2em;
        }
    }
</style>