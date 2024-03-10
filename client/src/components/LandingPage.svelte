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
    let realSliderValue = 10;
    let compareSliderValue;
    $: compareSliderValue = (Math.max(Math.min(realSliderValue, 100), 0)).toString();
    let lastKnownScrollPosition = 0;
    let rotating_text;
    let wrapper;

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
        if(!$register_button_visible || window.screen.width < 900) return;
        const middleX = wrapper.offsetLeft + startSection.offsetLeft + startSection.offsetWidth / 2;
        const middleY = wrapper.offsetTop + startSection.offsetTop + startSection.offsetHeight / 2;
        const offsetX = ((event.clientX + document.documentElement.scrollLeft - middleX) / middleX) * 45;
        const offsetY = ((event.clientY + document.documentElement.scrollTop - middleY) / middleY) * 45;
        console.log(middleX, middleY);
        console.log(event.clientX, event.clientY, offsetX, offsetY);

        startSection.animate({
            transform: `perspective(5000px) rotateY(${Math.max(Math.min(offsetX, 35), -35)}deg) rotateX(${Math.max(Math.min(offsetY, 35), -35) * -1}deg)`
        }, { duration: 1000, fill: "forwards" });
    }

    function update3DRotationScroll(event) {
        if(!$register_button_visible || window.screen.width >= 900) return;

        const middleY = startSection.offsetTop + startSection.offsetHeight / 2;
        const offsetY = (((document.documentElement.scrollTop + window.screen.height / 2 - 80) - middleY) / middleY) * 45;

        startSection.animate({
            transform: `perspective(5000px) rotateY(0deg) rotateX(${Math.max(Math.min(offsetY, 80), -80) * -1 + 'deg'})`
        }, {duration: 50, fill: "forwards"});
    }

    function addToSlider(event) {
        let deltaY = window.scrollY - lastKnownScrollPosition;
        lastKnownScrollPosition = window.scrollY;

        realSliderValue = realSliderValue + deltaY/10;
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
<svelte:window on:scroll={() => {update3DRotationScroll(); addToSlider()}}></svelte:window>

<div style="display: flex; flex-direction: column; gap: 2rem; position: relative;" bind:this={wrapper}>
    <div class="bubble-container">
        <div class="bubble one"></div>
        <div class="bubble two"></div>
        <div class="bubble three"></div>
    </div>
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
        <div style="display: flex; flex-direction: row; gap: 2rem; align-items: center; margin-bottom: 2rem;">
            <h2 class="responsive-heading">Pläne <span class="fancy-text" data-text="unlocked">unlocked</span></h2>
            <div style="display: flex;align-items: center;justify-content: center;">
                <span use:viewport
                      on:enterViewport={() => setTimeout(() => lockVisible = true, 800)}
                      on:exitViewport={() => lockVisible = false}
                      class:unlocked={lockVisible} class="lock" style="--locked-color: #ff8888; --unlocked-color: #ffffff"></span>
            </div>
        </div>
        <div class="presentation">
            <h2 class="responsive-heading" style="color: rgb(120, 120, 120)">Klassenplan<br>Wahrer Lehrerplan<br>Raumplan</h2>
            <div class="compare-slider">
                <div class="bg"></div>
                <div class="fg" style="width: {compareSliderValue}%"></div>
                <input type="range" min="1" max="100" value={compareSliderValue} on:input={(evt) => realSliderValue = parseFloat(evt.target.value)} class="slider" name='slider' id="slider">
                <button type="button" style="left: calc({compareSliderValue}% - 18px)" tabindex="-1">
                    <div class="arrows"></div>
                </button>
            </div>
        </div>
        <div class="presentation reverse">
            <h2 class="responsive-heading" style="color: rgb(150, 150, 150)">Freie Räume</h2>
            <img src="/public/base_static/images/landing_page/vplanfr_room_overview.png" alt="Raum-Übersicht in Better VPlan">
        </div>
    </section>
    <section>
        <h2 class="responsive-heading">
            Mobile Daten übrig für
            <div style="position: relative; color: transparent; display: inline-block;">
                Wichtigeres
                <div bind:this={rotating_text} class="rotating-text"
                     use:viewport
                     on:enterViewport={() => setTimeout(() => {rotating_text.style.setProperty('--transform-val', '-300%')}, 1500)}
                     on:exitViewport={() => {}}>
                    <span>WhatsApp</span>
                    <span>Discord</span>
                    <span>Spotify</span>
                    <span>Wichtigeres</span>
                </div>
            </div>
        </h2> <!-- Scrollt durch Whatsapp, Discord, Spotify, wichtigeres -->
        <div class="circle-bg" style="display: flex; justify-content: center;">
            <div style="display: flex; flex-direction: column; gap: 1rem; font-size: min(5vw, 1.4rem);" class="responsive-text">
                <span style="filter: drop-shadow(0px 0px 4px black)">🚀 4x weniger API-Requests als die VpMobil24 App</span>
                <span style="filter: drop-shadow(0px 0px 4px black)">⚡ Near-instant Ladezeiten</span>
                <span style="filter: drop-shadow(0px 0px 4px black)">🚵‍♂️ Funktioniert genauso offline (mit Planstatusindikatoren)</span>
            </div>
        </div>
    </section>
    <section>
        <h2 class="responsive-heading"><span class="fancy-text" data-text="Quality">Quality</span> of Life</h2>
        <!-- Solo leveling fenster gelb lila magenta + so dreck auf den fenstern vibe -->
        <div class="design-showcase">
            <div>
                <h2 class="responsive-heading">Clean</h2>
                <h2 class="responsive-heading">Customizable</h2>
                <h2 class="responsive-heading">Design</h2>
            </div>
        </div>
        <div class="favorite-showcase">
            <h2 class="responsive-heading">Beliebig viele Favoriten</h2>
            <img alt="Favorite Showcase" src="/public/base_static/images/landing_page/favorite_showcase.png">
        </div>
        <br><br>
        <ul class="responsive-text">
            <li>Alle Vorkommen von Klassen, Räumen, Lehrern etc. führen bei klicken zu ihrem jeweiligen Plan</li>
            <li>Überblick über alte Pläne</li>
            <li><a href="https://games.vplan.fr/">GAMES :DDD</a></li>
        </ul>
    </section>
    <section>
        <div style="height: 10px; width: auto; overflow: hidden; border-radius: 9vw; margin-top: 2rem; margin-bottom: 2rem;">
            <hr style="margin: 0; border-top: solid 10px; border-image: repeating-linear-gradient(-75deg, #fcd53f, #fcd53f 10px, #533566 10px, #533566 20px) 20;">
        </div>
        <h2 class="responsive-heading">Geplante Features 🚧</h2>
        <ul class="responsive-text">
            <li>Push Notifications</li>
            <li>Kalendersynchronisation</li>
            <li>Wochenplan</li>
        </ul>
    </section>
</div>

<style lang="scss">
  .favorite-showcase {
    padding: 2rem;
    border-radius: 4rem;
    overflow: hidden;
    display: flex;
    flex-direction: row;
    justify-content: space-around;
    align-items: center;
    position: relative;
    z-index: 0;
    background: radial-gradient(circle at left 0%, var(--background) 20%, transparent 50%);

    &::before {
      z-index: -1;
      content: "";
      position: absolute;
      inset: 0;
      background: url('/public/base_static/images/landing_page/favorite_burst.png');
      background-size: contain;
      background-position: 0 50%;
      background-repeat: no-repeat;
    }

    @media only screen and (max-width: 900px) {
      flex-direction: column;
      justify-content: center;

      &::before {
        background-position: 50% 0;
      }
      padding: 0.5rem;
      border-radius: 2rem;
    }

    img {
      max-height: 23rem;
      border-radius: 1rem;
      box-shadow: 5px 5px 15px rgb(10, 10, 10);
    }
  }

  .design-showcase {
    position: relative;
    padding-top: 10rem;
    padding-bottom: 10rem;
    @media only screen and (max-width: 900px) {
      padding-top: 5rem;
      padding-bottom: 5rem;
    }
    background: radial-gradient(circle, var(--background) 20%, transparent 50%);
    z-index: 0;

    &::before {
      z-index: -1;
      content: "";
      position: absolute;
      inset: 0;
      background: url('/public/base_static/images/landing_page/chaos_bg.png');
      background-size: contain;
      background-position: 50% 50%;
      background-repeat: no-repeat;
      animation: rotate 200s linear infinite;
    }

    & > div {
      display: flex;
      flex-direction: column;
      gap: 2rem;

      & > h2 {
        text-align: center;
        font-size: var(--font-size-xxl)
      }
    }

    img {
      position: absolute;
      inset: 0;
    }
  }
  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
  .rotating-text {
    position: absolute;
    inset: 0;
    mask-image: linear-gradient(to bottom, transparent 0%, black 20%, black 80%, transparent 100%);
    display: flex;
    flex-direction: column;
    color: white;
    --transform-val: 0%;

    span {
      transition: transform 2s cubic-bezier(0, 0, 0.5, 1);
      transform: translateY(var(--transform-val));
    }
  }
  .bubble-container {
    position: absolute;
    height: 60vh;
    width: 100%;
    z-index: 999;
    pointer-events: none;

    .bubble {
      position: absolute;
      aspect-ratio: 1;
      border-radius: 999vw;
      backdrop-filter: blur(5px);
      background: radial-gradient(circle, rgba(0,0,0,0) 0%, var(--bubble-color) 100%);

      &.one {
        top: 0;
        left: 0;
        transform: translate(-50%, -40%);
        width: 6rem;
        --bubble-color: rgba(202, 41, 255, 0.4);
      }
      &.two {
        top: 50%;
        right: 0;
        transform: translate(60%, -50%);
        width: 10rem;
        --bubble-color: rgba(63, 101, 255, 0.4);

        @media only screen and (max-width: 900px) {
          top: 30%;
          width: 8rem;
        }
      }
      &.three {
        bottom: 0;
        will-change: left;
        left: 35%;
        transform: translate(45%, 55%);
        width: 3rem;
        --bubble-color: rgba(67, 126, 253, 0.4);

        @media only screen and (max-height: 350px) {
          left: 13%;
          width: 3rem;
        }
      }
    }
  }
  .plans {
    .presentation {
      width: auto;
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 4rem;

      @media only screen and (min-width: 900px) {
        flex-direction: row;
        &.reverse {
          flex-direction: row-reverse;
        }
        justify-content: space-around;
      }

      img {
        $height: 80vh;
        height: $height;
        width: calc($height * 360 / 770);
        aspect-ratio: 360 / 770;
        border-radius: 1rem;
        overflow: hidden;
        -webkit-mask-image: -webkit-radial-gradient(white, black);
      }
    }
  }
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

      &::before {
        content: "";
        position: absolute;
        z-index: 0;
        inset: -5px;
        border-radius: 99vw;
        background: linear-gradient(180deg, purple, #6200ff);
        filter: blur(5px);
      }

      .arrows {
          @include center;
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
      background-color: rgb(0, 33, 179);
      background-image: url("/public/base_static/images/landing_page/start_bg.webp");
      background-size: cover;
      background-position: 50% 50%;
      box-sizing: border-box;
      border: 2px solid var(--accent-color);
      border-radius: 1rem;
      overflow: hidden;

      transform-style: preserve-3d;
  }
    .circle-bg {
      background-color: #6e6e80;
      background-image: radial-gradient(circle at center center, rgb(154, 82, 242), #110043), repeating-radial-gradient(circle at center center, rgb(154, 82, 242), var(--background), 10px, transparent 20px, transparent 10px);
      background-blend-mode: multiply;
      border-radius: 2rem;
      padding: 2rem;
      position: relative;

      &::before {
        content: "";
        position: absolute;
        z-index: -1;
        inset: -5px;
        border-radius: 2rem;
        background: linear-gradient(180deg, purple, #6200ff);
        filter: blur(20px);
        opacity: 0.4;
      }
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