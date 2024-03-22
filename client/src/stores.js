import { writable } from "svelte/store";

export const indexed_db = writable();
export const title = writable("");
export const logged_in = writable(false);
export const current_page = writable("plan");
export const settings = writable({});
export const active_modal = writable("");
export const notifications_list = writable([]);
export const pwa_prompt = writable();
export const new_changelogs_available = writable(false);
export const favorites = writable([]);
export const selected_favorite = writable(0);
export const api_base = writable("");
export const inspecting_lesson = writable(null);
export const inspecting_plan_type = writable(null);
export const inspecting_day = writable(null);

export const register_button_visible = writable(false);