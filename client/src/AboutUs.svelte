<script>
    import { onMount } from "svelte";
    import { title } from "./stores";

    onMount(() => {
        location.hash = "#about_us";
        title.set("Über uns");
    });
</script>

<main>
    <h1 class="responsive-heading">Über uns</h1>
    <p class="responsive-text">
        Wir sind drei Nerds, die sich dachten, dass der VpMobil24-App einige wichtige Features fehlen. Also haben wir diese Website mit den fehlenden Features programmiert. Offensichtlich ist sie nicht perfekt, über Vorschläge für Features und Design freuen wir uns immer! Schreibt uns dafür einfach auf Discord, unsere Tags stehen unter unseren Profilbildern.
    </p>
    <div class="third_wrapper">
        <div class="third">
            <img src="/base_static/images/about/bela.webp" alt="belissimo_t Profilbild">
            <span class="responsive-text bold">belissimo_t</span>
        </div>
        <div class="third">
            <img src="/base_static/images/about/Brot.webp" alt="officialbrot Profilbild">
            <span class="responsive-text bold">officialbrot</span>
        </div>
        <div class="third">
            <img src="/base_static/images/about/_qrtrenH.webp" alt="_qrtrenH Profilbild">
            <span class="responsive-text bold">_qrtrenh</span>
        </div>
    </div>
    <p class="responsive-text">
        Man kann uns per Mail unter <a href="mailto:elanus4506@gmail.com">elanus4506@gmail.com</a> erreichen.
    </p>
</main>

<style lang="scss">
    .responsive-heading {
        font-size: clamp(1.3rem, 4vw, 2.3rem);
        line-height: 1.3;
        margin-bottom: 15px;
        font-weight: 700;
    }

    .bold {
        font-weight: 700 !important;
    }
    
    .responsive-text {
        font-size: clamp(0.8rem, 3vw, 1.5rem);
        line-height: 1.6;
        margin-bottom: 15px;
        font-weight: 400;
    }

    .third_wrapper {
        display: flex;
        flex-direction: row;
        width: 100%;
        margin-top: 30px;
        margin-bottom: 10px;
    }

    .third {
        width: 33.33%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    img {
        width: 50%;
        aspect-ratio: 1;
        object-fit: contain;
        border-radius: 999vw;
        margin-bottom: 15px;
    }

    a {
        color: var(--accent-color);
    }
</style>