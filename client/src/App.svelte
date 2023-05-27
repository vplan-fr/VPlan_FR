<script>
	export let name;
    let lessons = [
    ]
    function load_lessons(school_num, date, plan_type, entity) {
        fetch(`./api/v69.420/${school_num}/plan?date=${date}`)
            .then(response => response.json())
            .then(data => {
                lessons = data["plans"][plan_type + "_plan"][entity];
                console.log(lessons);
            })
            .catch(error => {
                console.error(error);
        });
    }
    load_lessons("10001329", "2023-05-22", "form", "JG12");
    console.log(lessons)
</script>

<main>
	<h1>Hello {name}!</h1>
    {#each lessons as lesson}
        <div class="card lesson-head">{lesson.begin}-{lesson.end} (#{lesson.period})</div>
        <div class="card">{lesson.form}</div>
        <div class="card">{lesson.current_subject}</div>
        <div class="card">{lesson.current_teacher}</div>
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