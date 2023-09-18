import {current_page, settings} from "./stores.js";

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
            if (typeof house === "string") {
                out += `${house} `;
            } else {
                out += `Haus ${house}`;
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
            console.error("Einstellungen konnten nicht geladen werden.");
        })
}

export function navigate_page(page_id) {
    current_page.set(page_id);
    location.hash = `#${page_id}`;
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


function get_cache_keys() {
    let cache_keys = [];
    for ( var i = 0, len = localStorage.length; i < len; ++i ) {
        cache_keys.push(localStorage.key(i))
    }
    return cache_keys
}

export function should_date_be_cached(date) {
    const dateParts = date.split("-");
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1;
    const day = parseInt(dateParts[2]);
    const parsedDate = new Date(year, month, day);

    const currentDate = new Date();

    const currentDay = currentDate.getDay();
    const daysUntilLastSaturday = currentDay === 6 ? 1 : currentDay + 1; // Adjust for Saturday being the start of the week
    const lastSaturday = new Date(currentDate);
    lastSaturday.setDate(currentDate.getDate() - daysUntilLastSaturday);

    return parsedDate >= lastSaturday;
}

export function clear_caches() {
    let cache_keys = get_cache_keys();
    for (const ind in cache_keys) {
        let cache_key = cache_keys[ind];
        if (cache_key === "logged_in" || cache_key === "school_num" || cache_key.endsWith("_meta")) {
            continue;
        }
        let cur_date = cache_key.split("_")[1];
        if (!should_date_be_cached(cur_date)) {
            localStorage.removeItem(cache_key);
        }
    }
}

export function format_date(date) {
    date = new Date(date);

    const months = [
        "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
        "August", "September", "Oktober", "November", "Dezember"
    ];

    const day = date.getDate();
    const monthIndex = date.getMonth();
    const year = date.getFullYear();

    return `${day}. ${months[monthIndex]} ${year}`;

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
        return `${formatted_date} (Aktuellste)`
    }
    return formatted_date
}

export function analyze_local_storage() {
    function calculateSizeInBytes(value) {
        const str = JSON.stringify(value);
    return new Blob([str]).size;
    }

    for (let i = 0; i < localStorage.length; i++) {
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