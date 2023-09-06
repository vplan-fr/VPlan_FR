<script>
    import { onMount } from "svelte";
    import { title } from "./stores";

    onMount(() => {
        location.hash = "#about_us";
        title.set("Über uns");
    });
</script>

<main>
    <h1>Über uns</h1>
    <p>
        Wir sind drei Nerds, die sich dachten, dass der VpMobil24-App einige wichtige Features fehlen. Also haben wir diese Website mit den fehlenden Features programmiert. Offensichtlich ist sie nicht perfekt, über Vorschläge für Features und Design freuen wir uns immer! Schreibt uns dafür einfach auf Discord, unsere Tags stehen unter unseren Profilbildern.
    </p>
    <div class="third_wrapper">
        <div class="third">
            <img src="/base_static/images/about/bela.webp" alt="">
        </div>
        <div class="third">
            <img src="/base_static/images/about/Brot.png" alt="">
        </div>
        <div class="third">
            <img src="/base_static/images/about/_qrtrenH.jpeg" alt="">
        </div>
    </div>
    <p>
        Man kann uns per Mail unter <a href="mailto:elanus4506@gmail.com">elanus4506@gmail.com</a> erreichen.
    </p>
</main>

<style lang="scss">
    img {
        width: 100px;
        border-radius: 50px;
        border: 2px solid #906df5;
    }
</style>