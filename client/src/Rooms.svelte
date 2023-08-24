<script>
    import {group_rooms} from "./utils.js";

    export let rooms_data;
    export let all_rooms;
    export let plan_type;
    export let plan_value;

</script>

<div>
    <h1>Freie Räume</h1>
    {#if rooms_data?.free_rooms_by_block == null}
        <h1>Nicht verfügbar.</h1>
    {:else}
        {#each Object.entries(rooms_data.free_rooms_by_block) as [block, free_rooms]}
            <div class="block">
                <h2>Block {block}</h2>
                {#each group_rooms(Object.fromEntries(free_rooms.map(r => [r, all_rooms[r]]))) as [category, rooms]}
                    <h3>{category}</h3>
                    {#each rooms as room}
                        <!--{group_rooms()}-->
                        <button class="chip" on:click={() => {
                            plan_type = 'rooms';
                            plan_value = room;
                        }}>
                            <span>{room}</span>
                        </button>
                    {/each}
                {/each}
            </div>
        {/each}
    {/if}


</div>

<style lang="scss">
  @import 'theme.scss';

  .block {
    margin-bottom: 20px;
  }

  .chip {
    display: inline-block;
    padding: 5px 5px;
    margin: 0 10px 10px 0;
    outline: black 1px solid;
    width: 64px;
    /*height: 50px;*/
    /*font-size: 16px;*/
    //line-height: 50px;
    border-radius: 9999px;
    background-color: $background;

    span {
      // text color
        color: white;
    }
  }
</style>