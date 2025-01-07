<script>
    import Select from "../../base_components/Select.svelte";
    import Dropdown from "../../base_components/Dropdown.svelte";
    import {settings, selected_favorite} from "../../stores.js";
    import {format_timestamp} from "../../utils.js";

    export let exams;
    export let info;
    export let revision_arr;
    export let is_default_plan;
    export let last_fetch;
    export let selected_revision;
    export let date;
    export let plan_type;
    export let plan_value;
    export let text_color = "default";
</script>

{#if exams && Object.keys(exams).length !== 0}
    <div class="additional-info exams" class:default_text_color={text_color === "default"}>
        {#each Object.entries(exams) as [form, exam_list]}
            {#if exam_list.length > 0}
                <div class="inline-wrapper">
                    Klausuren für <button on:click={() => {
                            plan_type = "forms";
                            plan_value = form;
                            selected_favorite.set(-1);
                        }} class="no-btn-visuals clickable">{form}</button>:
                    <ul>
                        {#each exam_list as exam}
                            <li>{exam.course} bei <button on:click={() => {
                                        plan_type = "teachers";
                                        plan_value = exam.course_teacher;
                                        selected_favorite.set(-1);
                                    }} class="no-btn-visuals clickable" style="color: var(--text-color); font-size: inherit; margin-top: 0.3em;">{exam.course_teacher}</button>: {exam.begin} Uhr ({exam.duration}min)</li>
                        {/each}
                    </ul>
                </div>
            {:else}
                <div class="info-spacer"></div>
            {/if}
        {/each}
    </div>
{/if}
{#if info}
    {#if info.additional_info.length > 0}
        <div class="additional-info" class:default_text_color={text_color === "default"}>
            {#each info.processed_additional_info as info_paragraph}
                {#if info_paragraph.length > 0}
                    <div class="inline-wrapper">
                        {#each info_paragraph as text_segment}
                            {#if text_segment.link?.value.length === 1}
                                <button class="no-btn-visuals" on:click={() => {
                                        date = text_segment.link.date;
                                        plan_type = text_segment.link.type;
                                        plan_value = text_segment.link.value[0];
                                        selected_favorite.set(-1);
                                    }}>
                                    <div class="clickable">{text_segment.text}</div>
                                </button>
                            {:else if text_segment.link?.value.length >= 2}
                                <div class="fit-content-width">
                                    <Dropdown small={true} transform_origin_x="50%">
                                        <button slot="toggle_button" let:toggle on:click={toggle} class="toggle-button">
                                            <span class="grow">{text_segment.text}</span>
                                            <span class="material-symbols-outlined dropdown-arrow">arrow_drop_down</span>
                                        </button>

                                        {#each text_segment.link.value as item}
                                            <button on:click={() => {
                                                    date=text_segment.link.date;
                                                    plan_type = text_segment.link.type;
                                                    plan_value = item;
                                                    selected_favorite.set(-1);
                                                }}>{item}</button>
                                        {/each}
                                    </Dropdown>
                                </div>
                            {:else}
                                {text_segment.text}
                            {/if}
                        {/each}
                    </div>
                {:else}
                    <div class="info-spacer"></div>
                {/if}
            {/each}
        </div>
    {/if}
    <div class="last-updated">
        {#if !is_default_plan}Plan zuletzt aktualisiert: <span class="custom-badge">{format_timestamp(info.timestamp)}</span><br>{/if}
        Zuletzt auf neue Pläne überprüft: <span class="custom-badge">{format_timestamp(last_fetch)}</span>
    </div>
    <!-- Select Revision (Plan Version) -->
    {#if $settings.show_revision_selector && revision_arr.length > 0}
        <Select data={revision_arr} bind:selected_id={selected_revision} data_name="Revisions">Zeitstempel des Planuploads auswählen</Select>
    {/if}
{/if}

<style lang="scss">
  .additional-info {
    position: relative;
    font-size: var(--font-size-base);
    line-height: 1.5;
    border: clamp(1px, .3vmax, 3px) solid rgba(255, 255, 255, 0.2);
    padding: 10px;
    padding-top: calc(10px + var(--font-size-md) / 2);
    margin-top: 30px;
    border-radius: 5px;

    &.default_text_color::before {
      color: rgba(255, 255, 255, 0.2);
    }

    &::before {
      content: "Informationen";
      font-size: var(--font-size-md);
      color: var(--text-color);
      background: var(--background);
      padding: 0px 5px;
      position: absolute;
      top: 0;
      left: 20px;
      transform: translateY(-50%);
      border-radius: 5px;
    }

    &.exams::before {
      content: "Klausuren";
    }
  }

  .inline-wrapper > * {
    font-size: inherit;
    color: var(--text-color);
    white-space: pre-wrap;
    word-break: break-word;
  }

  .info-spacer {
    height: .5em;
  }

  .fit-content-width {
    width: fit-content;
  }

  .fit-content-width .dropdown-wrapper button, .max-width .dropdown-wrapper button {
    border: none;
    background: transparent;
    color: var(--text-color);
    transition: background-color .2s ease;
    width: 100%;
    padding: 2px 0px 2px 5px;
    font-size: inherit;

    &:hover, &:focus-visible {
      background-color: rgba(0, 0, 0, 0.5);
    }

    &.toggle-button {
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 5px;
      overflow: hidden;
      text-align: left;
      font-size: inherit;
      font-weight: inherit;
      color: var(--text-color);

      span.grow {
        flex: 1;
        white-space: nowrap;
      }

      &.center-align {
        text-align: center;
      }

      &:hover, &:focus-visible {
        background-color: rgba(255, 255, 255, 0.15);
      }
    }
  }

  .no-btn-visuals {
    border: 0;
    background: none;
    padding: 0;
    margin: 0;
    text-align: start;
  }

  .clickable {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 5px;
    padding: 2px 5px;
    transition: background-color 0.2s ease;

    &:hover, &:focus-visible {
      background-color: rgba(255, 255, 255, 0.2);
    }
  }

  .last-updated {
    font-size: var(--font-size-base);
    line-height: 1.5;
    margin-top: 20px;
    display: block !important;
  }

  .custom-badge {
    display: inline-flex;
    flex-direction: row;
    column-gap: .3em;
    align-items: center;

    background: rgba(255, 255, 255, 0.07);
    padding: 2px 7px;
    border-radius: 5px;
    white-space: nowrap;
    margin-bottom: .2em;
  }
</style>