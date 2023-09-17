<script>
    import {customFetch} from "./utils.js";
    import {notifications} from "./notifications.js";

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

<h1>Kontaktiere uns</h1>
<label for="category">Nachrichtenkategorie</label>
<select name="category" id="" bind:value={category}>
    <option value="bug">Bug</option>
    <option value="enhancement">Feature-Request</option>
    <option value="authorization">Schulauthorisierung</option>
    <option value="advertisement">Werbung</option>
    <option value="sponsoring">Sponsoren</option>
    <option value="questions">Fragen zur Website</option>
    <option value="else">Sonstiges</option>
</select>
<br>
<label for="person"></label>
<select name="person" id="" bind:value={person}>
    <option value="student">Schüler</option>
    <option value="teacher">Lehrer</option>
    <option value="head_teacher">Schulleiter</option>
    <option value="developer">Developer</option>
    <option value="else">Sonstige</option>
</select>
<br>
Deine Kontaktdaten: (Telefon/E-Mail)
<input type="text" bind:value={contact_data}>
<br>
Deine Nachricht:
<input type="text" bind:value={message}>
<br>

<button on:click={send_message}>Absenden</button>

<style lang="scss">

</style>