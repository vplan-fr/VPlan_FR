<script>
    import { onMount } from 'svelte';

    export let logged_in = false;
    let l_nickname;
    let l_password;
    let s_nickname;
    let s_password;
    let error_hidden = true;
    let error_message = "";
    let register_visible = false;

    onMount(() => {
        location.hash = "#login";
    });

    function login() {
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
                localStorage.setItem('logged_in', `${logged_in}`);
            })
            .catch(error => {
                console.error(error);
            }
        );
    }

    function signup() {

    }

    function toggle_form() {
        location.hash = location.hash === "#register" ? "#login" : "#register";
    }

    window.addEventListener('popstate', () => {
        register_visible = !(location.hash !== "#register");
    });

    $: register_visible = !(location.hash !== "#register");
</script>
<main class="center">
    <span class:hidden={error_hidden}>{error_message} <button on:click={() => {error_hidden = true}}>[X]</button></span><br>
    {#if !register_visible}
    <form on:submit|preventDefault={login}>
        <h1 class="unresponsive-heading">Login</h1>
        <input autocomplete="username" bind:value={l_nickname} label="Nutzername" minlength="3" maxlength="15" required class="textfield" placeholder="Nutzername"/>
        <input autocomplete="current-password" bind:value={l_password} label="Passwort" type="password" minlength="1" required class="textfield" placeholder="Passwort"/>
        <button class="default-button" type="submit">Login</button>
        <button on:click={toggle_form} class="link-button" type="button">Noch kein Account?</button>
        <button class="link-button" type="button" href="javascript:alert('Verkackt :D Aber da wir keine E-Mails zum Registrieren benutzen ist ein Passwort-Reset nicht möglich. Aber frag uns einfach und wir helfen dir beim wiederherstellen deiner Einstellungen & Präferenzen bei einem neuen Account.')">Passwort vergessen?</button>
    </form>
    {/if}
    {#if register_visible}
    <form on:submit|preventDefault={signup}>
        <h1 class="unresponsive-heading">Registrieren</h1>
        <input autocomplete="username" bind:value={s_nickname} label="Nutzername" minlength="3" maxlength="15" required class="textfield" placeholder="Nutzername"/>
        <input autocomplete="new-password" bind:value={s_password} label="Passwort" type="password" minlength="1" required class="textfield" placeholder="Passwort"/>
        <button type="submit">Registrieren</button>
    </form>
    {/if}
</main>
<style lang="scss">
    main::before {
        content: "";
        top: 0;
        left: 0;
        position: absolute;
        width: 100vw;
        height: 100vh;
        background-image: url('/base_static/images/blurry_gradient_bg.svg');
        background-repeat: no-repeat;
        background-size: cover;
        z-index: -1;
    }

    .center {
        display: grid;
        place-content: center;
        height: 100vh;
    }

    .hidden {
        display: none;
    }

    form {
        display: flex;
        flex-direction: column;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 5px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        min-width: min(400px, 70vw);
    }

    .unresponsive-heading {
        font-size: 3rem;
        line-height: 1.6;
        margin-bottom: 15px;
    }

    .textfield {
        width: 100%;
        padding: 12px 20px;
        margin-bottom: 8px;
        box-sizing: border-box;
        border: 2px solid white;
        border-radius: 3px;
    }

    .default-button {
        width: 100%;
        text-align: center;
        padding: 12px 20px;
        margin-bottom: 8px;
    }

    .link-button {
        display: inline-block;
        text-align: left;
        padding: 0;
        margin: 0;
        color: #3489E9;
        background: transparent;
        border: 0;
    }
</style>