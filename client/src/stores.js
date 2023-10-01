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
// TODO: as soon as this is connected to the endpoint, this needs to be cached and there needs to be a fallback
export const favourites = writable([
    {"school_num": "10000000", "name": "Mein Plan", "priority": 0, "plan_type": "forms", "plan_value": "12", "preferences": ["140", "97", "157", "96", "131", "88"]},
    {"school_num": "10000000", "name": "Plan von Freund", "priority": 0, "plan_type": "forms", "plan_value": "12", "preferences": ["140", "97", "157", "96", "130", "88"]},
    {"school_num": "10000000", "name": "Klassenlehrerplan", "priority": 0, "plan_type": "teachers", "plan_value": "Sipp", "preferences": []},
]);
export const selected_favourite = writable(0);
