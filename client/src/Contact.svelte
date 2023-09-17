<script>
    import {customFetch} from "./utils.js";
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
                notifications.success("Nachricht übermittelt")
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
]} bind:selected_id={person}>Person</Select>
<br><br>
Deine Kontaktdaten: (Telefon/E-Mail)<br>
<input type="text" bind:value={contact_data}>
<br><br>
Deine Nachricht:<br>
<input type="text" bind:value={message}>
<br>
<br>
<button on:click={send_message}>Absenden</button>

<style lang="scss">

</style>