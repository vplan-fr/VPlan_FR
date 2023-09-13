import { writable } from "svelte/store";

export const title = writable("");
export const logged_in = writable(false);
export const current_page = writable("school_manager");
export const settings = writable({});
export const preferences = writable({});