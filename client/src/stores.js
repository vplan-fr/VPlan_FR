import { writable } from "svelte/store";

export const title = writable("");
export const logged_in = writable(false);
export const current_page = writable("plan");
export const settings = writable(JSON.parse(localStorage.getItem("settings")) || {});
export const preferences = writable({});
export const active_modal = writable("");
export const notifications_list = writable([]);
export const pwa_prompt = writable();