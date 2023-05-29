<script>
  import { get } from "svelte/store";

    let name = "_qRtrenH&5367";
    let school_num = "10001329";
    const api_base = `./api/v69.420/${school_num}`;
    let meta = {};
    let lessons = [];
    let title = "";
    function get_meta() {
        fetch(`${api_base}/meta`)
            .then(response => response.json())
            .then(data => {
                meta = data;
                console.log(meta);
            })
            .catch(error => {
                console.error(error);
        });
    }
    function load_lessons(date, plan_type, entity) {
        title = `${plan_type}-plan for ${plan_type} ${entity}`
        fetch(`${api_base}/plan?date=${date}`)
            .then(response => response.json())
            .then(data => {
                console.log(data);
                lessons = data["plans"][plan_type][entity];
            })
            .catch(error => {
                console.error(error);
        });
    }
    get_meta();
    load_lessons("2023-05-22", "form_plan", "JG12");
</script>

<main>
	<h1>Hello {name}!</h1>
    <input id="inp_school_num" type="text" bind:value={school_num}>
    <br>
    <label for="rooms">Select a Room:</label>
    <select name="rooms" id="rooms">
    </select>
    <br>
    <br>
    <div>{title}</div>
    {#each lessons as lesson}
        <div class="card lesson-head">{lesson.begin}-{lesson.end} (#{lesson.period})</div>
        <div class="card clickable">
            <button on:click={load_lessons("2023-05-22", "form_plan", lesson.form)}>{lesson.form}</button>
        </div>
        <div class="card">{lesson.current_subject}</div>
        <div class="card clickable">
            <button on:click={load_lessons("2023-05-22", "teacher_plan", lesson.current_teacher)}>{lesson.current_teacher}</button>
        </div>
        <div class="card clickable">
            <button on:click={load_lessons("2023-05-22", "room_plan", lesson.rooms)}>{lesson.rooms}</button>
        </div>
        {#if lesson.info}
            <div class="card">{lesson.info}</div>
        {/if}
        <br>
    {/each}
	<p>Visit the <a href="https://svelte.dev/tutorial">Svelte tutorial</a> to learn how to build Svelte apps. <span class="material-symbols-outlined">settings</span></p>
    Lorem<br>ipsum<br>dolor<br>sit<br>amet<br>consectetur<br>adipisicing<br>elit.<br>Commodi<br>officia<br>natus<br>ad,<br>aut<br>accusantium<br>dolores<br>totam<br>veritatis<br>placeat<br>eligendi<br>repudiandae,<br>fugiat<br>facere<br>veniam<br>non<br>fugit<br>fuga<br>temporibus<br>optio<br>ex<br>deserunt.
    Lorem<br>ipsum<br>dolor<br>sit<br>amet<br>consectetur<br>adipisicing<br>elit.<br>Commodi<br>officia<br>natus<br>ad,<br>aut<br>accusantium<br>dolores<br>totam<br>veritatis<br>placeat<br>eligendi<br>repudiandae,<br>fugiat<br>facere<br>veniam<br>non<br>fugit<br>fuga<br>temporibus<br>optio<br>ex<br>deserunt.
</main>

<style lang="scss">
	main {
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
        .card {
            color: black;
            &.lesson-head {
                color: red;
            }
            &.clickable:hover {
                background-color: grey;
            }
        }
	}

	h1 {
		color: #ff3e00;
		text-transform: uppercase;
		font-size: 4em;
		font-weight: 100;
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>