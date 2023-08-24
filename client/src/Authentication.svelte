<script>
    import { TextField} from 'attractions';

    export let logged_in = false;
    let l_nickname;
    let l_password;
    let s_nickname;
    let s_password;
    let error_hidden = true;
    let error_message = "";

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


</script>
<main>
    <span class:hidden={error_hidden}>{error_message} <button on:click={() => {error_hidden = true}}>[X]</button></span><br>
    <form on:submit|preventDefault={login}>
        <h1 class="unresponsive-heading">Login</h1>
        <TextField bind:value={l_nickname} outline label="Nutzername" minlength="3" maxlength="15" required class="textfield"/>
        <TextField bind:value={l_password} outline label="Passwort" type="password" minlength="1" required class="textfield"/>
        <button>Login</button>
    </form>
    <form on:submit|preventDefault={signup}>
        <h1 class="unresponsive-heading">Registrieren</h1>
        <TextField bind:value={s_nickname} outline label="Nutzername" minlength="3" maxlength="15" required class="textfield"/>
        <TextField bind:value={s_password} outline label="Passwort" type="password" minlength="1" required class="textfield"/>
        <button>Registrieren</button>
    </form>
    <br>
    <a href="/logout">Logout</a><br>
    <!-- Authorize:
    <form action="/authorize" method="POST">
        <input name="school_num" id="school_number">
        <input name="username" id="username">
        <input name="pw" id="pw" type="password">
        <input type="submit">
    </form><br> -->
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

    :global(.textfield input) {
        color: white;
    }
    :global(.textfield input:hover) {
        border-color: white !important;
    }
    :global(.textfield input:hover + .label) {
        color: green !important;
    }
</style>