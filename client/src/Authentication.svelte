<script>
    import { onMount } from 'svelte';
    import {notifications} from './notifications.js';
    import { fly, fade } from 'svelte/transition';

    export let logged_in = false;
    let l_nickname;
    let l_password;
    let s_nickname;
    let s_password;
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
                    notifications.danger(data["error"], 2000);
                }
                localStorage.setItem('logged_in', `${logged_in}`);
            })
            .catch(error => {
                notifications.danger("Login fehlgeschlagen, Server nicht erreichbar!", 2000);
            }
        );
    }

    function signup() {
        let formData = new FormData();
        formData.append('nickname', s_nickname);
        formData.append('pw', s_password);
        fetch('/signup', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                logged_in = data["success"];
                if (!logged_in) {
                    notifications.danger(data["error"], 2000);
                }
                localStorage.setItem('logged_in', `${logged_in}`);
            })
            .catch(error => {
                notifications.danger("Registrieren fehlgeschlagen, Server nicht erreichbar!", 2000);
            }
        );
    }

    function toggle_form() {
        location.hash = location.hash === "#register" ? "#login" : "#register";
    }

    window.addEventListener('popstate', () => {
        register_visible = !(location.hash !== "#register");
    });

    $: register_visible = !(location.hash !== "#register");
</script>
<main transition:fade>
    {#if !register_visible}
    <form on:submit|preventDefault={login} transition:fly|local={{x:-500}}>
        <h1 class="unresponsive-heading">Login</h1>
        <label for="l_nickname">Nutzername</label>
        <div class="input_icon">
            <img src="/base_static/images/user-solid.svg" alt="User Icon">
            <input disabled={register_visible} autocomplete="username" name="l_nickname" bind:value={l_nickname} minlength="3" maxlength="15" required class="textfield" placeholder="Nutzername"/>
        </div>
        <label for="l_password">Passwort</label>
        <div class="input_icon">
            <img src="/base_static/images/lock-solid.svg" alt="Lock Icon">
            <input disabled={register_visible} autocomplete="current-password" name="l_password" bind:value={l_password} type="password" minlength="1" required class="textfield" placeholder="Passwort"/>
        </div>
        <button class="link-button" id="forgot_password" type="button" on:click={() => {alert('Verkackt :D Aber da wir keine E-Mails zum Registrieren benutzen ist ein Passwort-Reset nicht möglich. Aber frag uns einfach und wir helfen dir beim wiederherstellen deiner Einstellungen & Präferenzen bei einem neuen Account.')}}>Passwort vergessen?</button>
        <button class="default-button" type="submit">Login</button>
        <span>Noch kein Account? <button on:click={toggle_form} class="link-button" type="button">Registrieren</button></span>
    </form>
    {/if}
    {#if register_visible}
    <form on:submit|preventDefault={signup} transition:fly|local={{x:500}}>
        <button on:click={toggle_form} type="reset" id="back_button">←</button>
        <h1 class="unresponsive-heading">Registrieren</h1>
        <label for="s_nickname">Nutzername</label>
        <div class="input_icon">
            <img src="/base_static/images/user-solid.svg" alt="User Icon">
            <input disabled={!register_visible} autocomplete="username" name="s_nickname" bind:value={s_nickname} minlength="3" maxlength="15" required class="textfield" placeholder="Nutzername"/>
        </div>
        <label for="s_nickname">Passwort</label>
        <div class="input_icon">
            <img src="/base_static/images/lock-solid.svg" alt="Lock Icon">
            <input disabled={!register_visible} autocomplete="new-password" name="s_password" bind:value={s_password} type="password" minlength="10" required class="textfield" placeholder="Passwort"/>
        </div>
        <button class="default-button" type="submit">Registrieren</button>
    </form>
    {/if}
</main>
<style lang="scss">
    label {
        margin-bottom: 5px;
    }

    main::before {
        content: "";
        top: 0;
        left: 0;
        position: fixed;
        width: 100%;
        height: 100%;
        background-image: url('/base_static/images/blurry_gradient_bg.svg');
        background-repeat: no-repeat;
        background-size: cover;
        background-position-x: 50%;
        filter: brightness(1);
        z-index: -1;
    }

    #forgot_password {
        text-align: right;
        margin-bottom: 8px;
    }

    form {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        flex-direction: column;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 5px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        min-width: min(400px, 75vw);

        &::before {
            content: "";
            background-image: url('/base_static/images/logo.svg');
            background-size: contain;
            width: 90px;
            aspect-ratio: 1;
            position: absolute;
            top: -50px;
            left: 50%;
            transform: translate(-50%, -50%);
        }
    }

    .unresponsive-heading {
        font-size: 3rem;
        line-height: 1.6;
        margin-bottom: 15px;
    }

    .input_icon {
        position: relative;
        .textfield {
            padding-left: 40px;
        }
        img {
            position: absolute;
            top: 14px;
            left: 12px;
            width: 20px;
            height: 20px;
            background-size: contain;
            z-index: 1;
        }
    }

    .textfield {
        width: 100%;
        padding: 12px 20px;
        margin-bottom: 8px;
        box-sizing: border-box;
        border: 2px solid white;
        border-radius: 5px;
    }

    .default-button {
        width: 100%;
        text-align: center;
        padding: 12px 20px;
        margin-bottom: 8px;
        margin-top: 8px;
        border: 0;
        border-radius: 99vw;
        background: white;
        font-size: 1rem;
        font-weight: 500;
    }

    .link-button {
        display: inline-block;
        text-align: left;
        padding: 0;
        margin: 0;
        color: #0f0fff;
        background: transparent;
        border: 0;
        font-size: inherit;
    }

    #back_button {
        position: absolute;
        top: 0px;
        left: 5px;
        border: 0;
        background: none;
        color: white;
        font-size: 1.5rem;
    }
</style>