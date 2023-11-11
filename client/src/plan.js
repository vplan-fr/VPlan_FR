import {get_from_db, customFetch, cache_plan} from "./utils.js";

export function periods_to_block_label(periods) {
    periods.sort(function (a, b) {  return a - b;  });

    const rests = {
        0: "/Ⅱ",
        1: "/Ⅰ",
    };

    if (periods.length === 1) {
        return `${Math.floor((periods[0] - 1) / 2) + 1}${rests[periods[0] % 2]}`;
    } else if (periods.length === 2 && periods[0] % 2 === 1) {
        return `${Math.floor(periods[periods.length - 1] / 2)}`;
    } else {
        return periods.map(p => periods_to_block_label([p])).join(", ");
    }
}

export function sameBlock(a, b) {
    return a.includes(b[0]) || a.includes(b[1])
}

export function get_plan_version(data_from_cache, network_loading_failed, caching_successful) {
    return data_from_cache ? "cached" : !network_loading_failed ? caching_successful ? "network_cached" : "network_uncached" : null;
}

export function get_teacher_data(teacher_meta, teacher, school_num) {
    if (!teacher_meta) {
        return [null, null, null];
    }
    let full_teacher_name = teacher_meta[teacher]?.full_surname || teacher_meta[teacher]?.plan_long || null;
    let teacher_contact_link = teacher_meta[teacher]?.contact_link || null;
    let teacher_image_path = "/public/base_static/images/teachers/" + school_num + "/" + teacher_meta[teacher]?.image_path || null;
    teacher_image_path = teacher_meta[teacher]?.image_path || null;
    if (teacher_image_path) {
        teacher_image_path = `/public/base_static/images/teachers/${school_num}/${teacher_image_path}`;
    }
    return [full_teacher_name, teacher_contact_link, teacher_image_path];
}

export function load_plan(
    api_base,
    school_num,
    date, 
    revision=".newest", 
    enabled_dates, 
    last_updated_handler, 
    loading_state_updater, 
    plan_data_handler, 
    abort_controller_renewer) {

    if (enabled_dates === null || enabled_dates === undefined) {
        return;
    }
    if (date === null || date === undefined || !enabled_dates.includes(date)) {
        return;
    }

    loading_state_updater("loading", true);
    let loading = true;
    let fake_online = false;
    loading_state_updater("data_from_cache", false);
    loading_state_updater("cache_loading_failed", false);
    loading_state_updater("network_loading_failed", false);
    let network_loading_failed = false;
    loading_state_updater("caching_successful", false);
    let tmp_controller = abort_controller_renewer();
    let signal = tmp_controller.signal;
    // Try to load from cache
    if (revision === ".newest") {
        get_from_db(school_num, date, (data) => {
            data = data.plan_data;
            if(loading || network_loading_failed || fake_online) {
                plan_data_handler(data);

                if(!fake_online) {
                    loading_state_updater("cache_loading_failed", false);
                    loading_state_updater("data_from_cache", true);
                }
                loading_state_updater("loading", false);
                loading = false;
            }
        }, () => {
            loading_state_updater("cache_loading_failed", true);
            console.error("Cache loading failed!");
        });
    }

    let curr_time = new Date();
    if(!last_updated_handler(date, false) || curr_time - last_updated_handler(date, false) > 30_000) {
        // Try to load from network
        let params = new URLSearchParams();
        params.append("date", date);
        params.append("revision", revision);
        customFetch(`${api_base}/plan?${params.toString()}`, {signal: signal})
            .then(data => {
                if (Object.keys(data).length !== 0 && revision === ".newest") {
                    cache_plan(school_num, date, data, () => {
                        loading_state_updater("caching_successful", true);
                        last_updated_handler(date, true);
                    });
                }
                plan_data_handler(data);
                
                loading_state_updater("loading", false);
                loading = false;
                loading_state_updater("network_loading_failed", false);
                network_loading_failed = false;
                loading_state_updater("data_from_cache", false);
            })
            .catch(error => {
                console.log(error.message);
                loading_state_updater("loading", false);
                loading = false;
                loading_state_updater("network_loading_failed", true);
                network_loading_failed = true;
        });
    } else {
        fake_online = true;
        loading_state_updater("data_from_cache", false);
        loading_state_updater("network_loading_failed", false);
        loading_state_updater("caching_successful", true);
    }
}

export function gen_location_hash(location_name, school_num, date, plan_type, plan_value) {
    if(school_num && date && plan_type) {
        return `#${location_name}|${school_num}|${date}|${plan_type}|${plan_value}`;
    } else if(school_num && date) {
        return `#${location_name}|${school_num}|${date}`;
    } else {
        return `#${location_name}`
    }
}

export function load_lessons(data, plan_type, plan_value, use_grouped_form_plans, meta, plan_var_resetter, update_lessons) {
    // Check if settings and data are loaded
    if(use_grouped_form_plans === undefined || data === undefined) {
        return;
    }
    // Check the presence of necessary variables
    if (!plan_type || ((plan_type !== "room_overview") && !plan_value)) {
        plan_var_resetter();
        return;
    }
    // Check the validity of the plan type
    if(!["forms", "rooms", "teachers", "room_overview"].includes(plan_type)) {
        plan_var_resetter();
        return;
    }
    // Check the validity of the plan value
    if((plan_type === "rooms" || plan_type === "teachers") && (!Object.keys(meta[plan_type]).includes(plan_value))) {
        if (meta.school_num === school_num) {
            plan_var_resetter();
            return;
        }
    } else if((plan_type === "forms") && !Object.keys(meta.forms.forms).includes(plan_value)) {
        if (meta.school_num === school_num) {
            plan_var_resetter();
            return;
        }
    }

    let plan_key = use_grouped_form_plans ? "grouped_form_plans": "plans";
    update_lessons("rooms_data", data.rooms);
    if (plan_type !== "room_overview") {
        update_lessons("all_lessons", data[plan_key][plan_type] ? data[plan_key][plan_type][plan_value] || [] : []);
    }
}

export function apply_preferences(plan_type, preferences_apply, selected_favourite, favourites, lessons) {
    if (plan_type !== "forms") {
        return lessons
    }
    if (!preferences_apply) {
        return lessons
    }
    if (selected_favourite === -1) {
        return lessons
    }
    let cur_preferences = favourites[selected_favourite].preferences || [];
    let new_lessons = [];
    for (const lesson of lessons) {
        if (!(cur_preferences.includes(lesson.class_number))) {
            new_lessons.push(lesson);
        }
    }
    return new_lessons;
}