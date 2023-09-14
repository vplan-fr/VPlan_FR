<script>
    import { onMount } from 'svelte';
    import {notifications} from './notifications.js';
    import { fly, fade } from 'svelte/transition';
    import { logged_in, title } from './stores.js';
    import {customFetch} from "./utils.js";

    let l_nickname;
    let l_password;
    let s_nickname;
    let s_password;
    let register_visible = false;

    onMount(() => {
        location.hash = "#login";
        title.set("Login");
    });

    function login() {
        let formData = new FormData();
        formData.append('nickname', l_nickname);
        formData.append('pw', l_password);
        customFetch('/auth/login', {
            method: 'POST',
            body: formData,
        })
            .then(data => {
                $logged_in = true;
                localStorage.setItem('logged_in', `${$logged_in}`);
            })
            .catch(error => {
                $logged_in = false;
                localStorage.setItem('logged_in', `${$logged_in}`);
                notifications.danger(error);
            }
        );
    }

    function signup() {
        let formData = new FormData();
        formData.append('nickname', s_nickname);
        formData.append('pw', s_password);
        customFetch('/auth/signup', {
            method: 'POST',
            body: formData
        })
            .then(data => {
                $logged_in = true;
                localStorage.setItem('logged_in', `${$logged_in}`);
            })
            .catch(error => {
                $logged_in = false;
                localStorage.setItem('logged_in', `${$logged_in}`);
                notifications.danger(error);
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
    $: title.set(register_visible ? "Registrieren" : "Login");
</script>
<main transition:fade>
    {#if !register_visible}
    <form on:submit|preventDefault={login} transition:fly|local={{x:-500}}>
        <h1 class="responsive-heading">Login</h1>
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
        <span class="no-account-info">Noch kein Account? <button on:click={toggle_form} class="link-button" type="button">Registrieren</button></span>
    </form>
    {/if}
    {#if register_visible}
    <form on:submit|preventDefault={signup} transition:fly|local={{x:500}}>
        <button on:click={toggle_form} type="reset" id="back_button">←</button>
        <h1 class="responsive-heading">Registrieren</h1>
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
        <span class="extra-info">Mit dem Registrieren akzeptierst du alle unbedingt erforderlichen Cookies.</span>
        <button class="default-button" type="submit">Registrieren</button>
    </form>
    {/if}
</main>
<style lang="scss">
    .extra-info {
        font-size: var(--font-size-base);
        margin: 10px 0px;
    }

    .no-account-info {
        font-size: var(--font-size-base);
    }

    label {
        margin-bottom: 8px;
        font-size: var(--font-size-base);
    }

    main::before {
        content: "";
        top: 0;
        left: 0;
        position: fixed;
        width: 100%;
        height: 100%;
        background-image: url('/base_static/images/blurry_gradient_bg.svg');
        background-color: #906df5;
        background-repeat: no-repeat;
        background-size: cover;
        background-position-x: 50%;
        filter: brightness(1);
        z-index: -1;
    }

    #forgot_password {
        text-align: right;
    }

    form {
        position: absolute;
        top: 50%;
        left: calc(50% + (100vw - 100%) / 2);
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
        font-size: var(--font-size-sm);
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
        font-size: var(--font-size-base);
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
        font-size: var(--font-size-base);
    }

    #back_button {
        position: absolute;
        top: 0px;
        left: 5px;
        border: 0;
        background: none;
        color: white;
        font-size: var(--font-size-md);
    }
</style>