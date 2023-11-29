<script>
    import BarChart from "./BarChart.svelte";
    import Chart from "chart.js/auto";
    import { customFetch } from '../../utils.js';
    import {onMount} from "svelte";

    let monthly_signup_data = {};
    let settings_usage_data = {};


    function monthly_signups() {
        customFetch("/stats/monthly_signups")
            .then(data => {
                monthly_signup_data = data;
            })
    }
    function settings_usage() {
        customFetch("/stats/settings_usage")
            .then(data => {
                settings_usage_data = data;
                settings_usage_data = Object.fromEntries(
                    Object.entries(settings_usage_data).filter(([key, value]) => !key.includes("color"))
                );
            })
    }

    onMount(() => {
        monthly_signups();
        settings_usage();
    })

    $: console.log(settings_usage_data);


</script>
<h1 class="responsive-heading">Usage-Statistics</h1>

<h2 class="subheading">Monthly signups</h2>

<BarChart name="chart-monthly-signups" data={monthly_signup_data} label="Signups"/>

<h2 class="subheading">Settings usage</h2>
<div class="settings-chart-wrapper">
  {#each Object.keys(settings_usage_data) as setting}
    <div class="settings-chart">
      <h3 class="subsubheading">{setting}</h3>
      <BarChart name="{`chart-setting-${setting}`}"  data={settings_usage_data[setting]} label="Usage" type="pie"/>
    </div>
  {/each}
</div>



<style>
  .settings-chart-wrapper {
    margin-top: 20px;
    display: flex;
    flex-wrap: wrap;
  }
  .settings-chart {
    margin-bottom: 2rem;
    width: 25%;
  }
  .subheading {
    /* like h2 */
    margin-top: 20px;
    font-size: 1.5rem;
  }
  .subsubheading {
    /* like h3 */
    font-size: 1.25rem;
  }



</style>