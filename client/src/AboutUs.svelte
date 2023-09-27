<script>
    import { onMount } from "svelte";
    import { title } from "./stores";
    import Button from "./Components/Button.svelte";
    import {navigate_page} from "./utils.js";

    onMount(() => {
        location.hash = "#about_us";
        title.set("Über uns");
        // console.log("Mounted AboutUs.svelte");
    });
</script>

<main>
    <h1 class="responsive-heading">Über uns</h1>
    <div class="desktop">
        <p class="responsive-text">
            Wir sind drei Nerds, die sich dachten, dass der VpMobil24-App einige wichtige Features fehlen. Also haben wir diese Website mit den fehlenden Features programmiert. Offensichtlich ist sie nicht perfekt, über Vorschläge für Features und Design freuen wir uns immer! Schreibt uns dafür einfach auf Discord, unsere Tags stehen unter unseren Profilbildern.
        </p>
        <div class="third_wrapper">
            <div class="third" data-msg="Project Lead">
                <img src="/public/base_static/images/about/_qrtrenH.webp" alt="_qrtrenH Profilbild">
                <span class="responsive-text">_qrtrenh</span>
            </div>
            <div class="third" data-msg="Frontend Dev">
                <img src="/public/base_static/images/about/Brot.webp" alt="officialbrot Profilbild">
                <span class="responsive-text">officialbrot</span>
            </div>
            <div class="third" data-msg="Backend Dev">
                <img src="/public/base_static/images/about/bela.webp" alt="belissimo_t Profilbild">
                <span class="responsive-text">belissimo_t</span>
            </div>
        </div>
        <p class="responsive-text">
            Man kann uns mit unserem <Button class="inline" on:click={() => navigate_page("contact")} small={true}>Kontaktformular</Button> oder per Mail unter <a href="mailto:elanus4506@gmail.com">elanus4506@gmail.com</a> erreichen.
            <br>
            Hier ist außerdem unser <a href="https://github.com/ArtrenH/VPlan_FR">Github-Repository</a>.
        </p>
    </div>
</main>

<style lang="scss">
    :global(.inline) {
        display: inline !important;
    }

    .third_wrapper {
        display: flex;
        flex-direction: row;
        width: 100%;
        margin-top: 30px;
        margin-bottom: 10px;
    }

    .third {
        position: relative;
        width: 33.33%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        
        span {
            font-weight: 700;
        }

        &::after {
            content: attr(data-msg);
            display: block;
            position: absolute;
            top: 0;
            left: 50%;
            transform: translate(-50%, -25%);
            color: var(--text-color);
            font-size: var(--font-size-sm);
            background: var(--accent-color);
            border-radius: 5px;
            padding: 5px;
            opacity: 0;
            transition: all .2s ease;
            @media only screen and (min-width: 1501px) {
                font-size: var(--font-size-md);
                transform: translateX(0%);
            }
        }

        &:hover::after {
            transform: translate(-50%, -50%);
            opacity: 1;
            @media only screen and (min-width: 1501px) {
                transform: translateX(25%);
            }
        }
    }

    img {
        width: 50%;
        aspect-ratio: 1;
        object-fit: contain;
        border-radius: 999vw;
        margin-bottom: 7px;
    }

    a {
        color: var(--accent-color);
    }
</style>