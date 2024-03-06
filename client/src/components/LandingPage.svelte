<script>
    import { fade } from 'svelte/transition';
    import { onMount } from "svelte";
    import { title, register_button_visible } from "../stores";
    import Button from "../base_components/Button.svelte";
    import {navigate_page} from "../utils.js";

    onMount(() => {
        location.hash = "";
        title.set("Startseite");
        // console.log("Mounted AboutUs.svelte");
    });

    let intersectionObserver;
    let lockVisible = false;
    let mottos = [
        "vplan.fr, it's better... For real",
        "Yippee 🎉",
        "Deine Träume gehen in Erfüllung",
        "30 day no money back guarantee",
        "Ganz Mühlhausen fährt drauf ab (Angaben ohne Gewähr)",
        "Jetzt schon (oder eines Tages) an deiner Schule"
    ]
    let currentMottoIndex = 0;
    let startSection;
    let fg_img;
    let slider_btn;

    setTimeout(updateCurrentMottoIndex, 5000);
    function updateCurrentMottoIndex() {
        currentMottoIndex = (currentMottoIndex+1) % mottos.length;
        setTimeout(updateCurrentMottoIndex, 5000);
    }

    function ensureIntersectionObserver() {
        if (intersectionObserver) return;

        intersectionObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    const eventName = entry.isIntersecting ? 'enterViewport' : 'exitViewport';
                    entry.target.dispatchEvent(new CustomEvent(eventName));
                });
            }
        );
    }

    function update3DRotation(event) {
        if(!$register_button_visible) return;
        const middleX = startSection.offsetLeft + startSection.offsetWidth / 2;
        const middleY = startSection.offsetTop + startSection.offsetHeight / 2;
        const offsetX = ((event.clientX - middleX) / middleX) * 45;
        const offsetY = (((event.clientY - 30) - middleY) / middleY) * 45;

        startSection.animate({
            transform: `perspective(5000px) rotateY(${Math.min(offsetX, 35) + 'deg'}) rotateX(${Math.min(offsetY, 35) * -1 + 'deg'})`
        }, { duration: 1000, fill: "forwards" });
    }

    function viewport(element) {
        ensureIntersectionObserver();

        intersectionObserver.observe(element);

        return {
            destroy() {
                intersectionObserver.unobserve(element);
            }
        }
    }
</script>

<svelte:body on:mousemove={update3DRotation}></svelte:body>

<div style="display: flex; flex-direction: column; gap: 2rem;">
    <section class="start" bind:this={startSection}>
        <h1 class="responsive-heading">
            Better VPlan
        </h1>
        {#key currentMottoIndex}
            <p style="text-align: center; margin-bottom: 1.5rem;" in:fade>
                {mottos[currentMottoIndex]}
            </p>
        {/key}
        <div use:viewport
             on:enterViewport={() => $register_button_visible = true}
             on:exitViewport={() => $register_button_visible = false}>
            <Button background="var(--accent-color)" on:click={() => navigate_page('login')}>
                Anmelden
            </Button>
        </div>
    </section>
    <section class="plans">
        <div style="display: flex; flex-direction: row; gap: 2rem; align-items: center;">
            <h2 class="responsive-heading">Pläne <span class="fancy-text" data-text="unlocked">unlocked</span></h2>
            <div style="display: flex;align-items: center;justify-content: center;">
                <span use:viewport
                      on:enterViewport={() => setTimeout(() => lockVisible = true, 800)}
                      on:exitViewport={() => lockVisible = false}
                      class:unlocked={lockVisible} class="lock" style="--locked-color: #ff8888; --unlocked-color: #ffffff"></span>
            </div>
        </div>
        <div style="display: flex; flex-direction: column; align-items: center; width: auto;">
            <h2 class="responsive-heading" style="color: rgb(80, 80, 80)">Klassenplan</h2>
            <div class="compare-slider">
                <div class="bg"></div>
                <div class="fg" bind:this={fg_img}></div>
                <input type="range" min="1" max="100" value="20" on:input={(evt) => {
                    fg_img.style.width = evt.target.value + "%";
                    slider_btn.style.left = "calc(" + evt.target.value + "% - 18px)"}} class="slider" name='slider' id="slider">
                <button type="button" bind:this={slider_btn} tabindex="-1"></button>
            </div>
        </div>
        <!--
            Freie Räume, Lehrerplan, Raumplan, Klassenplan, Überblick über alte Pläne
        -->
    </section>
    <section>
        <h2 class="responsive-heading">Mobile Daten übrig für wichtigeres</h2> <!-- Scrollt durch Whatsapp, Discord, Spotify, wichtigeres -->
        <!--
            Daten für einen Tag heruntergeladen -> Alle Pläne verfügbar
            Funktioniert offline
        -->
        <div class="circle-bg" style="display: flex; justify-content: center;">
            <div style="display: flex; flex-direction: column; gap: 1rem; " class="responsive-text">
                <span style="filter: drop-shadow(0px 0px 4px black)">🚀 4x weniger API-Requests als die Indiware App</span>
                <span style="filter: drop-shadow(0px 0px 4px black)">⚡ Near-instant Ladezeiten</span>
                <span style="filter: drop-shadow(0px 0px 4px black)">🚵‍♂️ Funktioniert genauso offline (mit Planstatusindikatoren)</span>
            </div>
        </div>
    </section>
    <section>
        <h2 class="responsive-heading"><span class="fancy-text" data-text="Quality">Quality</span> of Life</h2>
        <!--
            Cooles Design
            Customizable
            GAMES :DDD
        -->
    </section>
    <section>
        <h2 class="responsive-heading">Geplante Features</h2>
        <!--
            Push Notifications
            Kalendersynchronisation
            Wochenplan
        -->
    </section>
</div>

<style lang="scss">
  .compare-slider {
    $height: 80vh;
    position: relative;
    height: $height;
    width: calc($height * 360 / 770);
    aspect-ratio: 360 / 770;
    border-radius: 1rem;
    overflow: hidden;
    -webkit-mask-image: -webkit-radial-gradient(white, black);

    & > div {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-size: calc((360 / 770) * $height) 100%;
    }
    .bg {
      background-image: url('/public/base_static/images/landing_page/vpmobil24_form_view.png');
    }
    .fg {
      background-image: url('/public/base_static/images/landing_page/vplanfr_form_view.png');
      width: 20%;
    }

    @mixin center() {
      display: flex;
      justify-content: center;
      align-items: center;
    }

    .slider {
      position: absolute;
      -webkit-appearance: none;
      appearance: none;
      width: 100%;
      height: 100%;
      background: transparent !important;
      outline: none;
      margin: 0;
      transition: all .2s;
      @include center;
      &::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 5px;
        height: $height;
        background: linear-gradient(180deg, purple, #6200ff);
        cursor: pointer;
        border-radius: 5vw;
      }
    }
    & > button {
      $size: 30px;
      border: 3px solid rgb(30, 30, 30);
      pointer-events: none;
      position: absolute;
      width: $size;
      height: $size;
      border-radius: 50%;
      background: rgb(50, 50, 50);
      left: calc(20% - 18px);
      top: calc(50% - 18px);
      @include center;

      @mixin arrow-helper() {
        content: '';
        padding: 3px;
        display: inline-block;
        border: solid white;
        border-width: 0 2px 2px 0;
      }
      &::after {
        @include arrow-helper();
        transform: rotate(-45deg);
      }
      &::before {
        @include arrow-helper();
        transform: rotate(135deg);
      }
    }
  }

  .fancy-text {
    position: relative;
    transform-style: preserve-3d;
    z-index: 0;
  }
    .fancy-text::before {
      content: attr(data-text);
      position: absolute;
      inset: 0;
      color: transparent;
      background: -webkit-linear-gradient(45deg, magenta, #0043ff);
      -webkit-background-clip: text;
      background-clip: text;
      z-index: -2;
      filter: blur(5px);
      font-weight: bolder;
      margin-top: 5px;
    }
    .start {
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      width: auto;
      min-height: 60vh;
      padding: 2rem;
      background-color: black;
      background-image: linear-gradient(134deg, rgba(80, 0, 179, 0.8) 20%, rgba(0, 33, 179, 0.6) 80%), url("data:image/svg+xml,%3Csvg viewBox='0 0 80 80 ' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='2.73' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E") !important;
      box-sizing: border-box;
      border: 2px solid var(--accent-color);
      border-radius: 1rem;
      overflow: hidden;

      transform-style: preserve-3d;
    }
    .circle-bg {
      background-color: #6e6e80;
      background-image: radial-gradient(circle at center center, rgb(138, 74, 217), #110043), repeating-radial-gradient(circle at center center, rgb(138, 74, 217), var(--background), 10px, transparent 20px, transparent 10px);
      background-blend-mode: multiply;
      border-radius: 2rem;
      padding: 2rem;
    }
    /* Locked */
    .lock {
      width: 24px;
      height: 21px;
      border: 3px solid var(--locked-color);
      border-radius: 5px;
      position: relative;
      -webkit-transition: all 0.2s ease-in-out;
      transition: all 0.2s ease-in-out;
    }
    .lock:after {
      content: "";
      display: block;
      background: var(--locked-color);
      width: 3px;
      height: 7px;
      position: absolute;
      top: 50%;
      left: 50%;
      margin: -3.5px 0 0 -2px;
      -webkit-transition: all 0.2s ease-in-out;
      transition: all 0.2s ease-in-out;
    }
    .lock:before {
      content: "";
      display: block;
      width: 10px;
      height: 10px;
      bottom: 100%;
      position: absolute;
      left: 50%;
      margin-left: -8px;
      border: 3px solid var(--locked-color);
      border-top-right-radius: 50%;
      border-top-left-radius: 50%;
      border-bottom: 0;
      -webkit-transition: all 0.2s ease-in-out;
      transition: all 0.2s ease-in-out;
    }
    /* Unlocked */
    .unlocked:before {
      bottom: 130%;
      left: 31%;
      margin-left: -11.5px;
      transform: scale(-1, 1);
    }
    .unlocked,
    .unlocked:before {
      border-color: var(--unlocked-color);
    }
    .unlocked:after {
      background: var(--unlocked-color);
    }
</style>