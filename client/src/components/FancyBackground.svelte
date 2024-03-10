<script>
    let blob;
    let clientX = 0;
    let clientY = 0;
    function moveBlob(event) {
        if(window.screen.width < 900) {return;}
        clientX = event["clientX"];
        clientY = event["clientY"];

        blob.animate({
            left: `${clientX + document.documentElement.scrollLeft}px`,
            top: `${clientY + document.documentElement.scrollTop}px`
        }, { duration: 2000, fill: "forwards" });
    }
    function moveScrollBlob(event) {
        if(window.screen.width >= 900) {return;}
        blob.animate({
            left: `${window.screen.width/2 + document.documentElement.scrollLeft}px`,
            top: `${window.screen.height/2 + document.documentElement.scrollTop}px`
        }, { duration: 6000, fill: "forwards" });
    }
</script>

<svelte:body on:mousemove={moveBlob}></svelte:body>
<svelte:window on:scroll={moveScrollBlob}></svelte:window>
<svelte:head>
    <style>
        body {
            position: relative;
        }
    </style>
</svelte:head>

<div id="bg"></div>

<div id="blob-container">
    <div id="blob" bind:this={blob}></div>
</div>

<style lang="scss">
    #bg {
        height: 100%;
        width: 100%;
        position: absolute;
        z-index: -1;
        background-image:  radial-gradient(#666666 0.5px, transparent 0.5px), radial-gradient(#666666 0.5px, transparent 0.5px);
        background-repeat: repeat;
        background-size: 20px 20px;
        background-position: 0 0, 10px 10px;
    }

    #blob {
        height: 34vmax;
        aspect-ratio: 1;
        position: absolute;
        left: 50%;
        top: 50%;
        translate: -50% -50%;
        border-radius: 50%;
        background: white linear-gradient(to right, var(--accent-color), blue);
        animation: rotate 20s infinite;
        opacity: 0.6;
        filter:blur(3vmax);
    }
    #blob-container {
      height: 100%;
      width: 100%;
      position: absolute;
      z-index: -2;
      overflow: hidden;
    }
    @keyframes rotateBlob {
        from {
            rotate: 0deg;
        }

        50% {
            scale: 1 1.5;
        }

        to {
            rotate: 360deg;
        }
    }
</style>