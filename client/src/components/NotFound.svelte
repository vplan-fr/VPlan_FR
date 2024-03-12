<script>
    import {onMount} from "svelte";
    import {replace_page} from "../utils.js";
    import {current_page, logged_in, title} from "../stores.js";

    onMount(() => {
        title.set("Seite nicht gefunden");
        const protected_routes = [
            "plan",
            "weekplan",
            "school_manager",
            "favorite",
            "favorites",
            "pwa_install",
            "stats"
        ];
        let tmp_location = $current_page.split("|")[0];
        if((tmp_location === "login") || (tmp_location === "register")) {
            replace_page("plan");
        }
        else if(protected_routes.includes(tmp_location)) {
            replace_page("login");
        }
    });
</script>

<div style="display: flex; flex-direction: column; gap: 2rem; width: auto; min-height: 50vh; justify-content: center; align-items: center;">
    <span class="material-symbols-outlined fancy-text" style="font-size: max(3rem, 5vw)">travel_explore</span>
    <span class="responsive-text" style="text-align: center;">Wir haben weit und breit gesucht aber nichts gefunden. ☹️</span>
</div>

<style lang="scss">
    .fancy-text {
      background: linear-gradient(310deg, #cc33ff, #3358ff, #33bbff);
      color: transparent;
      -webkit-background-clip: text;
      background-clip: text;
      background-size: 600% 600%;

      -webkit-animation: colorScroll 3s ease infinite;
      -moz-animation: colorScroll 3s ease infinite;
      animation: colorScroll 3s ease infinite;
    }

    @-webkit-keyframes colorScroll {
      0%{background-position:0% 50%}
      50%{background-position:100% 50%}
      100%{background-position:0% 50%}
    }
    @-moz-keyframes colorScroll {
      0%{background-position:0% 50%}
      50%{background-position:100% 50%}
      100%{background-position:0% 50%}
    }
    @keyframes colorScroll {
      0%{background-position:0% 50%}
      50%{background-position:100% 50%}
      100%{background-position:0% 50%}
    }
</style>