import { writable } from "svelte/store";

export const indexed_db = writable();
export const title = writable("");
export const logged_in = writable(false);
export const current_page = writable("plan");
export const settings = writable({});
export const preferences = writable({});
export const active_modal = writable("");
export const notifications_list = writable([]);
export const pwa_prompt = writable();
export const new_changelogs_available = writable(false);