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
            out += `Haus ${house}`;
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
    });
}