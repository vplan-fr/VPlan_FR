<script>
    export let logged_in = false;
    let nickname;
    let password;
    let error_hidden = true;
    let error_message = "";

    function login() {
        console.log("trying to log in")
        let formData = new FormData();
        formData.append('nickname', nickname);
        formData.append('pw', password);
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
    <span class:hidden={error_hidden}>{error_message} <button on:click={() => {error_hidden = true}}>[X]</button></span>
    Login / Signup:<br>
    <input bind:value={nickname}>
    <input type="password" bind:value={password}>
    <button on:click={login}>Login</button>
    <button on:click={signup}>Sign up</button>
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
</style>