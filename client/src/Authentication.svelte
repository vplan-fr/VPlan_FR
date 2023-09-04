<script>
    export let logged_in = false;
    let l_nickname;
    let l_password;
    let s_nickname;
    let s_password;
    let error_hidden = true;
    let error_message = "";
    let register_visible = false;

    function login() {
        console.log("trying to log in")
        let formData = new FormData();
        formData.append('nickname', l_nickname);
        formData.append('pw', l_password);
        fetch('/login', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                logged_in = data["success"];
                if (!logged_in) {
                    error_hidden = false;
                    error_message = data["error"];
                }
            })
            .catch(error => {
                console.error(error);
            }
        );
    }

    function signup() {

    }

    function toggle_form() {

    }
</script>
<main>
    <span class:hidden={error_hidden}>{error_message} <button on:click={() => {error_hidden = true}}>[X]</button></span><br>
    {#if !register_visible}
    <form on:submit|preventDefault={login}>
        <h1 class="unresponsive-heading">Login</h1>
        <input bind:value={l_nickname} label="Nutzername" minlength="3" maxlength="15" required class="textfield" placeholder="Nutzername"/>
        <input bind:value={l_password} label="Passwort" type="password" minlength="1" required class="textfield" placeholder="Passwort"/>
        <!-- svelte-ignore a11y-invalid-attribute -->
        <a href="javascript:alert('Verkackt :D Aber da wir keine E-Mails zum Registrieren benutzen ist ein Passwort-Reset nicht möglich. Aber frag uns einfach und wir helfen dir beim wiederherstellen deiner Einstellungen & Präferenzen bei einem neuen Account.')">Passwort vergessen?</a>
        <button class="default-button">Login</button>
        <!-- svelte-ignore a11y-missing-attribute -->
        <span>Noch kein Account? <button on:click={toggle_form} class="link-button">Registrieren</button></span>
    </form>
    {/if}
    {#if register_visible}
    <form on:submit|preventDefault={signup}>
        <h1 class="unresponsive-heading">Registrieren</h1>
        <input bind:value={s_nickname} label="Nutzername" minlength="3" maxlength="15" required class="textfield" placeholder="Nutzername"/>
        <input bind:value={s_password} label="Passwort" type="password" minlength="1" required class="textfield" placeholder="Passwort"/>
        <button>Registrieren</button>
    </form>
    {/if}
    <br>
    <a href="/logout">Logout</a><br>
</main>
<style lang="scss">
    .hidden {
        display: none;
    }
    form {
        display: flex;
        flex-direction: column;
    }

    .unresponsive-heading {
        font-size: 3rem;
        line-height: 1.6;
        margin-bottom: 15px;
    }

    .textfield {
        width: 100%;
        padding: 12px 20px;
        margin: 8px 0px;
        box-sizing: border-box;
        border: 2px solid white;
        border-radius: 3px;
    }

    .default-button {
        width: 100%;
        text-align: center;
        padding: 12px 20px;
    }
    .link-button {
        display: inline-block;
        padding: 0;
        margin: 0;
        color: blue;
    }
</style>