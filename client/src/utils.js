import {current_page, indexed_db, logged_in, register_button_visible, settings} from "./stores.js";
import {notifications} from "./notifications.js";
import { get } from "svelte/store";
import { favorites } from "./stores.js";

const MAX_CACHED_PLANS = 10; // 2 Weeks

export function group_rooms(rooms) {
    let _grouped_rooms = {};
    for (let [room, data] of Object.entries(rooms)) {
        let category = JSON.stringify([data?.house, data?.floor]);

        if (_grouped_rooms[category] === undefined) {
            _grouped_rooms[category] = [];
        }
        _grouped_rooms[category].push(room);
    }

    let out = Object.entries(_grouped_rooms).map(([category, rooms]) => [JSON.parse(category), rooms]);

    let sort_key = (house, floor) => {
        if (house === null) {
            return 1000;
        }
        if (typeof house === "string") {
            house = house.charCodeAt(0);
        }
        if (floor === null) {
            floor = 10;
        }
        return house * 10 + floor;
    }

    out.sort(([[house1, floor1], _], [[house2, floor2], __]) => {
        return sort_key(house1, floor1) - sort_key(house2, floor2);
    });
    out.map(([_, curr_rooms]) => curr_rooms.sort((room1, room2) => rooms[room1]?.room_nr - rooms[room2]?.room_nr));

    function get_category_name([house, floor]) {
        let out = "";
        if (house != null) {
            if (("" + house).length === 1 || typeof house !== "string") {
                out += `Haus ${house}`;
            } else {
                out += `${house} `;
            }
        }
        if (floor != null) {
            out += ` / Etage ${floor}`;
        }
        if (out.length === 0) {
            out = "Sonstige";
        }
        return out;
    }

    return out.map(([category, rooms]) => [get_category_name(category), rooms]);
}


function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

export async function customFetch(url, options = {}) {
    if(!navigator.onLine) {
        throw Error("Diese Funktion ist offline nicht verfügbar");
    }
    const headers = {
        "X-CSRFToken": getCookie("csrftoken")
    };

    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            ...headers,
        },
    })
        .then(response => {
            if (!response.ok) {
                console.log(`Got the followoing non-ok response at url ${url}`, response);
                throw new Error("Ein Netzwerkfehler ist aufgetreten");
            }
            return response.json()
        })
        .then(data => {
            if (!data.success) {
                console.log(`Got the following error stream at url ${url}`, data);
                throw new Error(data.error);
            }
            return data.data;
        })
        .catch(error => {
            if (error.name === "TypeError" && error.message === "NetworkError when attempting to fetch resource.") {
                console.log(`NetworkError at url ${url}`)
                throw new Error("Ein Netzwerkfehler ist aufgetreten");
            }
            throw error;
        })
}


export function get_settings() {
    customFetch("/auth/settings")
        .then(data => {
            settings.set(data);
        })
        .catch(error => {
            settings.set(JSON.parse(localStorage.getItem("settings")));
            console.error("Einstellungen konnten nicht geladen werden.");
        })
}

export function navigate_page(page_id) {
    if(page_id === "plan" && get(current_page).startsWith("plan")) {return;}
    current_page.set(page_id);
    location.hash = `#${page_id}`;
    register_button_visible.set(false);
    // console.log(`Changed Location to: "${page_id}"`);
}

export function update_colors(settings) {
    if(!settings) {return;}
    if(settings.background_color) {
        document.documentElement.style.setProperty('--background', settings.background_color);
    }
    if(settings.accent_color) {
        document.documentElement.style.setProperty('--accent-color', settings.accent_color);
    }
    if(settings.text_color) {
        document.documentElement.style.setProperty('--text-color', settings.text_color);
    }
    if(settings.cancelled_color) {
        document.documentElement.style.setProperty('--cancelled-color', settings.cancelled_color);
    }
    if(settings.rainbow) {
        if(navigator.userAgent.toLowerCase().includes('firefox')) {
            document.documentElement.style.setProperty('--background', 'var(--fallback-rainbow)');
        } else {
            document.documentElement.style.setProperty('--background', 'var(--rainbow)');
        }
    }
}

export function init_indexed_db() {
    // Check for support.
    if (!('indexedDB' in window)) {
        console.log("This browser doesn't support IndexedDB.");
        notifications.danger("Dein Browser unterstützt kein Plan-Caching!");
        return;
    }

    let request = indexedDB.open('plan-db', 1);
    request.onerror = (event) => {
        console.error("Couldn't open IndexedDB");
        notifications.danger("Konnte den Plan-Cache nicht öffnen!");
    };
    request.onsuccess = (event) => {
        indexed_db.set(event.target.result);
    };
    request.onupgradeneeded = (event) => {
        indexed_db.set(event.target.result);
        if (!get(indexed_db).objectStoreNames.contains('plan-store')) {
            const plan_store = get(indexed_db).createObjectStore('plan-store', {keyPath: ['school_num', 'date']});
            plan_store.createIndex('school_num', 'school_num');
            plan_store.createIndex('date', 'date');
            plan_store.createIndex('plan_data', 'plan_data');
        }
    }
}  

export function get_from_db(school_num, date, callback, error_callback = () => {}) {
    if(!get(indexed_db)) {
        error_callback();
        return;
    }

    const transaction = get(indexed_db).transaction(["plan-store"]);
    const store = transaction.objectStore("plan-store");
    const request = store.get([school_num, date]);
    request.onerror = (event) => {
        error_callback();
        console.error(event);
    };
    
    request.onsuccess = (event) => {
        if(request.result !== undefined) {
            callback(request.result);
        } else {
            error_callback();
        }
    };
}

export function get_school_plan_count(school_num, callback) {
    if(!get(indexed_db)) {
        return;
    }

    const tx = get(indexed_db).transaction(['plan-store']);
    
    tx.onerror = (event) => {
        console.log("Error while getting schools plan count", event);
    };

    const store = tx.objectStore('plan-store');
    const index = store.index("school_num");
    const request = index.getAll(school_num);
    request.onerror = (event) => {
        console.error(event);
    };

    request.onsuccess = (event) => {
        callback(request.result ? request.result.length : 0);
    };
}

export function cache_plan(school_num, date, data, callback) {
    if(!get(indexed_db)) {
        return;
    }

    get_from_db(school_num, date, () => {
        _indexed_db_add(school_num, date, data);
        callback();
    }, () => {
        get_school_plan_count(school_num, count => {
            if(count >= MAX_CACHED_PLANS) {
                delete_oldest_plan_before(school_num, date, result => {
                    if(result) {
                        _indexed_db_add(school_num, date, data);
                        callback();
                    } else {
                        // console.log("Couldn't cache plan.")
                        //notifications.danger("Plan konnte nicht gecached werden!")
                    }
                });
            } else {
                _indexed_db_add(school_num, date, data);
                callback();
            }
        });
    });
}

function _indexed_db_add(school_num, date, data) {
    if(!get(indexed_db)) {
        return;
    }

    const tx = get(indexed_db).transaction(['plan-store'], 'readwrite');

    // tx.oncomplete = (event) => {};
    
    tx.onerror = (event) => {
        console.log("Error while caching plan", event);
    };

    const store = tx.objectStore('plan-store');
    const item = {
        school_num: school_num,
        date: date,
        plan_data: data
    };
    store.put(item);
}

export function delete_oldest_plan_before(school_num, date, callback) {
    if(!get(indexed_db)) {
        return;
    }

    const tx = get(indexed_db).transaction(['plan-store']);
    
    tx.onerror = (event) => {
        console.log("Error while deleting oldest plan", event);
    };

    const store = tx.objectStore('plan-store');
    const index = store.index("school_num");
    const request = index.getAll(school_num);
    request.onerror = (event) => {
        console.error(event);
    };

    request.onsuccess = (event) => {
        let oldest_item = request.result.sort((a, b) => Date.parse(a.date) - Date.parse(b.date))[0];
        if(date > oldest_item.date) {
            _indexed_db_remove(oldest_item.school_num, oldest_item.date);
            callback(true);
            return;
        }
        callback(false);
    };
}

function _indexed_db_remove(school_num, date) {
    const tx = get(indexed_db).transaction(['plan-store'], 'readwrite');

    // tx.oncomplete = (event) => {};
    
    tx.onerror = (event) => {
        console.log("Error while removing plan", event);
    };

    const store = tx.objectStore('plan-store');
    store.delete([school_num, date]);
}

export function clear_plan_cache(callback=() => {}) {
    if(!get(indexed_db)) {
        return;
    }

    const tx = get(indexed_db).transaction(['plan-store'], "readwrite");
    
    tx.onerror = (event) => {
        console.log("Error while clearing cache", event);
    };

    const store = tx.objectStore('plan-store');
    const request = store.clear();
    request.onerror = (event) => {
        notifications.danger("Cache konnte nicht geleert werden");
        console.error(event);
    };

    request.onsuccess = (event) => {
        callback();
    };
}

export function format_date(date) {
    date = new Date(date);

    const months = [
        "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
        "August", "September", "Oktober", "November", "Dezember"
    ];

    const days = [
        "So",
        "Mo",
        "Di",
        "Mi",
        "Do",
        "Fr",
        "Sa"
    ];

    const weekday = days[date.getDay()];
    const day = date.getDate();
    const monthIndex = date.getMonth();
    const year = date.getFullYear();

    return `${weekday}., ${day}. ${months[monthIndex]} ${year}`;

}

export function format_revision_date(date, latest) {
    let date_obj;
    if (date === ".newest") {
        date_obj = new Date(latest);
    } else {
        date_obj = new Date(date);
    }

    const options = {
        year: "numeric",
        month: "2-digit",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    };

    let formatted_date = date_obj.toLocaleString("de-DE", options) + " Uhr";
    if (date === ".newest") {
        return `${formatted_date} (Aktuellste Version)`
    }
    return formatted_date
}

export function format_timestamp(timestamp) {
    const date = new Date(timestamp);

    const targetTimezone = 'Europe/Berlin';
    const options = {
        timeZone: targetTimezone,
        weekday: 'long',
        month: 'long',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    };
    const formatter = new Intl.DateTimeFormat('de-DE', options);
    const formattedDate = formatter.format(date).replace("um", "-") + " Uhr";

    return `${formattedDate}`;
}

export function analyze_local_storage() {
    function calculateSizeInBytes(value) {
        const str = JSON.stringify(value);
    return new Blob([str]).size;
    }

    for (let i = 0; i < to.length; i++) {
        const key = localStorage.key(i);
        const value = localStorage.getItem(key);
        const sizeInBytes = calculateSizeInBytes(value);
        console.log(`Key: ${key}, Size (bytes): ${sizeInBytes}`);
    }
    // Check available localStorage space in bytes
    function checkAvailableStorage() {
        if ('localStorage' in window && window['localStorage'] !== null) {
            try {
                const currentSize = JSON.stringify(localStorage).length;
                const totalSize = (1024 * 1024) * 5; // 5 MB (adjust as needed)
                const availableSpace = totalSize - currentSize;
                console.log(`Available localStorage space: ${availableSpace} bytes`);
            } catch (e) {
                console.error('localStorage is not available or accessible.');
            }
        } else {
            console.error('localStorage is not supported by this browser.');
        }
    }

    checkAvailableStorage();
}

export function arraysEqual(a, b) {
    if (a === b) return true;
    if (a == null || b == null) return false;
    if (a.length !== b.length) return false;

    a.sort(function (a, b) {
        return a - b;
    });
    b.sort(function (a, b) {
        return a - b;
    });

    for (var i = 0; i < a.length; ++i) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

export async function load_meta(school_num) {
    let meta_data;
    return customFetch(`/api/v69.420/${school_num}/meta`)
        .then(data => {
            try {
                localStorage.setItem(`${school_num}_meta`, JSON.stringify(data));
            } catch (error) {
                if (error.name === 'QuotaExceededError' ) {
                    notifications.danger("Die Schulmetadaten konnten nicht gecached werden.")
                } else {
                    throw error;
                }
            }
            meta_data = data;
            return [meta_data, false]
        })
        .catch(error => {
            meta_data = localStorage.getItem(`${school_num}_meta`);
            if (meta_data !== "undefined" && meta_data) {
                console.log("Metadaten aus Cache geladen");
                return [JSON.parse(meta_data), true];
            } else {
                console.log("Metadaten konnten nicht geladen werden.");
                notifications.danger(error.message);
            }
        })
}

export function get_favorites(callback = () => {}) {
    return customFetch("/api/v69.420/favorites")
        .then(data => {
            localStorage.setItem("favorites", JSON.stringify(data));
            favorites.set(data);
            callback();
        }).catch(error => {
            console.log("Favorites couldn't be loaded from server.");
            // check if favorites in localstorage
            if(!localStorage.getItem("favorites")) {
                favorites.set([]);
            } else {
                favorites.set(JSON.parse(localStorage.getItem("favorites")));
            }
            callback();
        })
}