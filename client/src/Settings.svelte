<script>

    let settings;
    let show_plan_toasts;
    let day_switch_keys;
    let background_color;
    let accent_color;
    function get_settings() {
        fetch("/settings")
            .then(response => response.json())
            .then(data => {
                settings = data;
                show_plan_toasts = settings["show_plan_toasts"];
                day_switch_keys = settings["day_switch_keys"];
                background_color = settings["background_color"];
                accent_color = settings["accent_color"];
            })
            .catch(error => {
                console.error(error);
            })
    }
    function change_settings() {
        fetch("/settings", {
            method: "POST",
            body: JSON.stringify(settings),
        })
            .then(response => response.json())
            .then(data => {

            })
            .catch(error => {
                console.error(error);
                get_settings();
            })
    }

    $: get_settings();
    $: settings = {
        "show_plan_toasts": show_plan_toasts,
        "day_switch_keys": day_switch_keys,
        "background_color": background_color,
        "accent_color": accent_color,
    }
    $: console.log(show_plan_toasts);
</script>

<main>
    <button on:click={change_settings}>Speichern</button>
    <br>
    show plan toasts: <input type="checkbox" bind:checked={show_plan_toasts}><br>
    day switch keys: <input type="checkbox" bind:checked={day_switch_keys}><br>
    background color: <input type="color" bind:value={background_color}><br>
    accent color: <input type="color" bind:value={accent_color}>
</main>

<style lang="scss">


</style>