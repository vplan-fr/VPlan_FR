<script>
    import {notifications} from './notifications.js';
    import {logged_in} from './stores.js';

    function logout() {
        fetch('/logout')
            .then(response => response.json())
            .then(data => {
                $logged_in = !data["success"];
                localStorage.setItem('logged_in', `${$logged_in}`);
                if ($logged_in) {
                    error_hidden = false;
                    error_message = data["error"];
                }
            })
            .catch(error => {
                notifications.danger("Logout fehlgeschlagen!", 2000);
            });
    }
</script>

<nav>
    <img class="logo" src="/base_static/images/better_vp_white.svg" alt="Better VPlan Logo">
    <ul class="nav-element-wrapper">
        <li><button on:click={logout}>Logout</button></li>
        <!-- <li><button on:click={togglePopup}>Manage Schools</button></li> -->
    </ul>
</nav>

<style lang="scss">
    nav {
        z-index: 999;
        background-color: var(--background-color);
        box-shadow: 0px 3px 4px rgba(0, 0, 0, 0.2);
        height: 64px;
        @media only screen and (max-width: 601px) {
            height: 56px;
            padding: 0px 5px;
        }
        overflow: hidden;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        padding: 0px 20px;
        box-sizing: border-box;

        &::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.07);
            pointer-events: none;
        }

        img.logo {
            box-sizing: border-box;
            height: 100%;
            padding: 10px;
            @media only screen and (max-width: 601px) {
                padding: 8px;
            }
        }

        .nav-element-wrapper {
            position: relative;
            display: flex;
            flex-direction: row;
            height: 100%;
            float: right;

            li {
                height: 100%;
                list-style-type: none;
                button {
                    height: 100%;
                    padding: 0 15px;
                    background-color: transparent;
                    border: none;
                    color: var(--text-color);
                    transition: background-color 200ms ease;

                    &:hover, &:focus-visible {
                        background-color: rgba(0, 0, 0, 0.3);
                    }
                }
            }
        }
    }
</style>