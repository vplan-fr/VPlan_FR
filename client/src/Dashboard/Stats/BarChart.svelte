<script>
    import {onMount} from "svelte";
    import Chart from 'chart.js/auto';

    export let name;
    export let data;
    export let label;
    export let type = 'bar';

    let options;
    if (type !== 'pie') {
        options = {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        };
    } else {
        options = {
        };
    }

    let myChart;
    let mounted = false;


    function createChart(name, data, label) {
        if (myChart) {
            myChart.destroy();
        }
        const ctx = document.getElementById(name).getContext('2d');
        let chart_data = {
            labels: Object.keys(data),
            datasets: [{
                label: label,
                data: Object.values(data),
                /*backgroundColor: null,
                borderColor: null,*/
                borderWidth: 1
            }]
        };
        myChart = new Chart(ctx, {
            type: type,
            data: chart_data,
            options: options,
        });
    }

    onMount(() => {
        mounted = true;
    });


    $: if (name && data && label) {
        if (mounted) {
            createChart(name, data, label);
        }
    }


</script>

<div>
    <canvas id="{name}" width="400" height="200"></canvas>
</div>
