document.getElementById("status").innerHTML = "HELLO WRLD";
var status_ = document.getElementById("status");

var canvas = document.getElementById("canvas");
var ctx = canvas.getContext("2d");
var zoom_level = 0;
var phys_width = 1000;
var phys_height = 1000;
var zoom_factor = 2;
var virt_x = 1000000;
var virt_y = 1000000;
var virt_width;
var virt_height;
var show_labels;
var show_hitboxes = true;
var show_reticule = true;
var show_grid = false;
var hitboxes = [];
var bookmarks = [];
var focused_celestial = null;
var chunks = [];
var i = 0;
var j = 0;
var active_shipments = [];
var min_virt_x;
var max_virt_x;
var min_virt_y;
var max_virt_y;

while (i <= 100) {
    j = 0;
    var this_chunk = [];
    while (j <= 100) {
        this_chunk.push([]);
        j++;
        }
    chunks.push(this_chunk);
    i++;
    }

zoom_level = 14;
virt_x = 5000000000000;
virt_y = 5000000000000;
// 10,000,000,000,000
var dragging = false;
canvas.addEventListener("mousedown", dragStart, false);
canvas.addEventListener("mousemove", drag, false);
canvas.addEventListener("mouseup", dragEnd, false);
var first_drag_position, second_drag_position;
canvas.addEventListener("dblclick", test, false);
canvas.addEventListener("click", clickcanvas, false);
canvas.addEventListener("wheel", wheeltest, false);

function add_bookmark(event) {
    if(focused_celestial) {
        bookmarks.push([focused_celestial, zoom_level]);
        console.log("added ", focused_celestial.name, zoom_level, " to bookmarks");
        }
    remake_bookmarks();
    }
function add_bookmark2(event) {
    if (focused_celestial) {
        add(focused_celestial, zoom_level);
        }
    }
function bookmark_buttom_press(event) {
    console.log("pressed bookmark button", event);
    }
function wheeltest(event) {
    event.preventDefault();
    if (event.deltaY > 0){
        zoom_level += 0.1;
        redraw();
        }
    if (event.deltaY < 0){
        zoom_level -= 0.2;
        redraw();
        }
    }

function clickcanvas(event) {
    var position = getCanvasCoordinates(event);
    var planet = get_celestial_from_phys_coord(position["x"], position["y"]);
    if (!(planet == null)){
        
        console.log("This is the planet", planet.name);
        status_.innerHTML = "This is the planet "  + planet.name;
        var celestial_name = document.getElementById("celestial_name");
        celestial_name.innerHTML = planet.name;
        
        }

    }

function test(event) {
    var position = getCanvasCoordinates(event);
    var planet = get_celestial_from_phys_coord(position["x"], position["y"]);
    if (!(planet == null)) {
        virt_x = planet.x;
        virt_y = planet.y;
        focused_celestial = planet;
        create_planet_dropdown(planet);
        redraw();
        return;
        }
    }

function get_celestial_from_phys_coord(x, y) {
    var planet = null;
    hitboxes.forEach(function(hb) {
        if (hb.west <= x && x < hb.east) {
            if (hb.north <= y && y < hb.south) {
                planet = hb.planet;
                return;
                }
            }
        });
    return planet;
    }

function dragStart(event) {
    first_drag_position = getCanvasCoordinates(event);
    dragging = true;

    }

function drag(event) {
    if (!dragging){
        return
        }
    }

function dragEnd(event) {
    var x_diff, y_diff;
    second_drag_position = getCanvasCoordinates(event);
    dragging = false;
    x_diff = second_drag_position["x"] - first_drag_position["x"];
    y_diff = second_drag_position["y"] - first_drag_position["y"];
    v1 = phys_to_virt(first_drag_position["x"], first_drag_position["y"]);
    v2 = phys_to_virt(second_drag_position["x"], second_drag_position["y"]);
    var virt_differences = phys_to_virt(x_diff, y_diff);
    virt_x -= (v2[0] - v1[0]);
    virt_y -= (v2[1] - v1[1]);
    redraw();
    }

function getCanvasCoordinates(event) {
    var x, y;
    x = event.clientX - canvas.getBoundingClientRect().left,
    y = event.clientY - canvas.getBoundingClientRect().top;
    return {x: x, y: y};
    }

ctx.fillStyle = "black";
ctx.fillRect(0, 0, canvas.width, canvas.height);
let socket = new WebSocket("ws://127.0.0.1:9000")
socket.onopen = function(e) {
    socket.send("cucumber");
    };

function toggle_grid() {
    if (show_grid == true) {
        show_grid = false;}
    else {show_grid = true}
    redraw();
    }

function draw_grid(){
    var width_exponent;
    var i, amount_of_lines;
    width_exponent = Math.round(Math.log10(virt_width))-1;
    height_exponent = Math.round(Math.log10(virt_height)) - 1;
    var virt_leftmost = virt_x - (virt_width/2);
    var virt_rightmost = virt_x + (virt_width/2);
    var phys_leftmost = virt_leftmost / (zoom_factor ** zoom_level * 1000000);

    var virt_topmost = virt_y - (virt_height/2);
    var virt_bottommost = virt_y + (virt_width/2);
    var phys_topmost = virt_topmost / (zoom_factor ** zoom_level * 1000000);
    
    ctx.fillStyle = "rgba(51, 170, 51, .7)";

    var interval_size = (10**width_exponent);
    var which_interval_left = Math.ceil(virt_leftmost / interval_size);
    which_interval_right = Math.floor(virt_rightmost / interval_size);
    i = which_interval_left;
    var phys_i;
    while (i <= which_interval_right) {
        phys_i = (((i*interval_size)-(virt_x - (virt_width/2))   )/(zoom_factor**zoom_level*1000000));
        ctx.moveTo(phys_i, 0);
        ctx.lineTo(phys_i, phys_height);
        ctx.stroke();
        i++;
        }

    interval_size = (10**height_exponent);
    var which_interval_top = Math.ceil(virt_topmost / interval_size);
    which_interval_bottom = Math.floor(virt_bottommost / interval_size);
    i = which_interval_top;
    var phys_i;
    while (i <= which_interval_bottom) {
        phys_i = (((i*interval_size)-(virt_y - (virt_height/2))   )/(zoom_factor**zoom_level*1000000));
        ctx.moveTo(0, phys_i);
        ctx.lineTo(phys_width, phys_i);
        ctx.stroke();
        i++;
        }
    }

function toggle_labels(){
    console.log("toggling labels");
    var checkbox = document.getElementById("label_check");
    if (checkbox.checked == true){
        show_labels = true;
        console.log("showing labels");
        }
    else {
        show_labels = false;
        console.log("hiding labels");
        }
    redraw();
    }

function toggle_hitboxes() {
    var checkbox = document.getElementById("hitbox_check");
    if (checkbox.checked == true) {
        show_hitboxes = true;
        }
    else {
        show_hitboxes = false;
        }
    redraw();
    }

function toggle_reticule() {
    var checkbox = document.getElementById("reticule_check");
    console.log("reticule toggled");
    if (checkbox.checked == true) {
        show_reticule = true;
        }
    else {
        show_reticule = false;
        }
    redraw();
    }

function Celestial(id, x, y, radius, color, is_star) {
    this.id = id;
    this.x = x;
    this.y = y;
    this.radius = radius;
    this.color = color;
    this.is_star = is_star;
    this.brilliance = Math.floor(Math.random() * 10);
    this.fruit = "banana";
}

class Celest {
    constructor(id, x, y, radius, color, is_star, parent_celestial) {
        this.id = id;
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.color = color;
        this.is_star = is_star;
        this.parent_celestial = parent_celestial;
        this.brilliance = Math.floor(Math.random() * 10);
        this.banana();
        this.option_element = document.createElement("option");
        if (!(parent_celestial==undefined)) {
            this.option_element.innerHTML = parent_celestial.name + "." + this.name;
            }
        else {
            this.option_element.innerHTML = this.name;
            }
        var p_element = document.createElement("p");
        this.option_element.appendChild(p_element);
        this.option_element.name = "test";
        }

    banana() {
        var amount_of_letters = Math.floor(Math.random()*8) + 4;
        this.name = "";
        var i = 0;
        var temp;
        var letter;
        var alphabet = "abcdefghijklmnopqrstuvwxyz";
        var which_letter;
        var name_letters = [];
        while (i<amount_of_letters){
            which_letter = Math.floor(Math.random()*26)
            name_letters.push(alphabet[which_letter]);
            i++;
            }
        this.name = name_letters.join("");

        }
    }

function zoom_in(){
    zoom_level -= 1;
    redraw();
    }

function zoom_out(){
    zoom_level += 1;
    redraw();
    }

function pan_left(){
    virt_x -= (virt_width/10);
    redraw();
    }

function pan_right(){
    virt_x += (virt_width/10);
    redraw();
    }

function pan_up(){
    virt_y-= (virt_width/10);
    redraw();
    }

function pan_down(){
    virt_y+= (virt_width/10);
    redraw();
    }

var star_data;

function redraw(){
    var pixel_height = Math.floor(10000000000000 / canvas.height);
    var pixel_width = Math.floor(10000000000000 / canvas.width);
    var x;
    var y;
//    var min_virt_x, min_virt_y, max_virt_x, max_virt_y;
    var within_x, within_y;
    var hitbox_coords;
    min_virt_x = virt_x - (virt_width/2)
    max_virt_x = virt_x + (virt_width/2)
    min_virt_y = virt_y - (virt_height/2);
    max_virt_y = virt_y + (virt_height/2);
    hitboxes = [];
   
    ctx.fillStyle = "black";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    if (show_grid == true){
        draw_grid();
        }
    virt_width = phys_width * zoom_factor ** zoom_level * 1000000;
    virt_height = phys_height * zoom_factor ** zoom_level * 1000000;
    //min_virt_x = virt_x - (virt_width/2);
    //min_virt_y = virt_y - (virt_height/2);
    //max_virt_x = virt_x + (virt_width/2);
    //max_virt_y = virt_y + (virt_height/2);
    if (show_reticule) {
        ctx.strokeStyle = "white";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(phys_width/2, phys_height/2, 30, 0, 2 * Math.PI);
        ctx.stroke();
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.strokeStyle = "yellow";
        ctx.moveTo(phys_width/2-30, phys_width/2-30);
        ctx.lineTo(phys_width/2-8, phys_width/2-8);
        ctx.stroke();
        ctx.moveTo(phys_width/2+30, phys_width/2-30);
        ctx.lineTo(phys_width/2+8, phys_width/2-8);
        ctx.stroke();
        ctx.moveTo(phys_width/2-30, phys_width/2+30);
        ctx.lineTo(phys_width/2-8, phys_width/2+8);
        ctx.stroke();
        ctx.moveTo(phys_width/2+30, phys_width/2+30);
        ctx.lineTo(phys_width/2+8, phys_width/2+8);
        ctx.stroke();
        };
    allstars.forEach(function(celestial){
        within_x = (min_virt_x <= celestial.x && celestial.x < max_virt_x);
        within_y = (min_virt_y <= celestial.y && celestial.y < max_virt_y);
        if (within_x && within_y && (celestial.brilliance + 4 >= zoom_level|| celestial.brilliance >= 0))
        {
            var coords;
            coords = draw_celestial(celestial);

            if (zoom_level <= 8 && show_labels == true){
                ctx.fillText(celestial.name, coords[0]-20, coords[1]-5);
                }

            if (zoom_level <= 8 && show_hitboxes == true) {
                hitbox_coords = [coords[0]-40, coords[1]-30, coords[0]+30, coords[1]+30];
                hitbox_ = new hitbox(celestial, coords[0]-30, coords[1]-30, coords[0]+30, coords[1]+30);
                hitboxes.push(hitbox_);
                ctx.strokeStyle = "white";
                ctx.beginPath();
                ctx.rect(coords[0]-30, coords[1]-30, 60, 60);
                ctx.stroke();
                }

            if (zoom_level <= 1 && celestial.is_star) {
                }

            if (zoom_level <= 1 && celestial.parent_celestial > -1 && !(celestial.parent_celestial == null)) {
                var parent_star;
                allstars.forEach(function(star){
                    if (star.id == celestial.parent_celestial) {
                        parent_star = star;
                        }
                    });

                ctx.strokeStyle = "gray";
                ctx.beginPath();
                var radius = parent_star.radius / (zoom_factor ** zoom_level * 1000000);
                var star_coords = virt_to_phys(parent_star.x, parent_star.y);
                var planet_coords = virt_to_phys(celestial.x, celestial.y);
                radius = Math.round(Math.sqrt((star_coords[0] - planet_coords[0])**2 + (star_coords[1] - planet_coords[1])**2));
                ctx.arc(star_coords[0], star_coords[1], radius, 0, Math.PI*2);
                ctx.stroke();
                }
            }
        }
    );
    active_shipments.forEach(function(shipment){
        draw_shipment(shipment);
        })
    status_.innerHTML = zoom_level;
}
function draw_shipment_line(a_coords, b_coords) {
    let phys_a_coords = null;
    let phys_b_coords = null;
    if (check_if_point_in_window(a_coords)) {
        phys_a_coords = virt_to_phys(...a_coords);
        }
    if (check_if_point_in_window(b_coords)) {
        phys_b_coords = virt_to_phys(...b_coords);
        }
    if (phys_a_coords && phys_b_coords) {
        draw_line(phys_a_coords, phys_b_coords);
        return;
        }

    var top_line, right_line, left_line, bottom_line;
    var all_intersections = []
    var valid_intersections = []
    let shipment_line = [a_coords, b_coords];
    top_line = [[min_virt_x, min_virt_y], [max_virt_x, min_virt_y]];
    bottom_line = [[min_virt_x, max_virt_y], [max_virt_x, max_virt_y]];
    left_line = [[min_virt_x, min_virt_y], [min_virt_x, max_virt_y]];
    right_line = [[max_virt_x, min_virt_y], [max_virt_x, max_virt_y]];
    var all_lines = [top_line, right_line, left_line, bottom_line];
    var which_boundary = 0;
    [top_line, right_line, left_line, bottom_line].forEach(function(boundary){
        let m = get_m(shipment_line); // what if directly vertical?
        let b = get_b(shipment_line, m);
        m = get_m(shipment_line);
        b = get_b(shipment_line, m);
        intersection = get_intersection(shipment_line, boundary, m, b, which_boundary);


        var relevant_line = all_lines[which_boundary];
        if ([0, 3].includes(which_boundary)) {
            if (relevant_line[0][0] <= intersection[0] && intersection[0] < relevant_line[1][0]) {
                //console.log("HHHHH ");
                valid_intersections.push(intersection);
                }
            else {
                }

            }
        else {
            if (relevant_line[0][1] <= intersection[1] && intersection[1] < relevant_line[1][1]) {
                //console.log("jjjjjj ");
                valid_intersections.push(intersection);
                }
            else {
                }
            }

        all_intersections.push(intersection);
        which_boundary++;
        });
    var virt_points = [a_coords, b_coords];
    var final_points = [];
    virt_points.forEach(function(endpoint) {
        if (check_if_point_in_window(endpoint)) {
            final_points.push(virt_to_phys(...endpoint));
            return;
            }
        else {
            var distance1;
            var distance2;
            distance1 = (valid_intersections[0][0] - endpoint[0])**2 + (valid_intersections[0][1] - endpoint[1])**2;
            distance2 = (valid_intersections[1][0] - endpoint[0])**2 + (valid_intersections[1][1] - endpoint[1])**2;
            if (distance1 <= distance2) {
                final_points.push(virt_to_phys(...valid_intersections[0]));
                }
            else {
                final_points.push(virt_to_phys(...valid_intersections[1]));
                }
            };
        });        
    draw_line(...final_points);
    }
function draw_shipment(shipment) {
    let source_id = shipment.source;
    let dest_id = shipment.destination;
    let source = shipment.source_obj
    let destination = shipment.destination_obj;;
    let current_coords = shipment.current_coords;
    ctx.strokeStyle = "green";
    draw_shipment_line([source.x, source.y], [destination.x, destination.y]);
    ctx.strokeStyle = "purple";
    ctx.lineWidth = 2;
    draw_shipment_line([source.x, source.y], shipment.current_coords);
    return;
    }
function get_intersection(line, boundary, m, b, which_boundary) {
    if (boundary[0][1] == boundary[1][1]) {
        b2 = boundary[0][1];
        x = (b2 - b) / m;
        return [x, b2];
        }
    else {
        N = boundary[0][0]; 
        y = N * m + b;
        return [N, y];
        }
    }
function get_m(line) {
    return (line[1][1]-line[0][1])/(line[1][0]-line[0][0])
    }
function get_b(line, m){
    point = line[0];
    return point[1] - m * point[0];
    }
function check_if_point_in_window(point) {
    if (min_virt_x <= point[0] && point[0] < max_virt_x  &&
        min_virt_y <= point[1] && point[1] < max_virt_y) {
            return true;
            }
    return false;

    }
function draw_line(source_coords, dest_coords){
    ctx.beginPath();
    ctx.moveTo(...source_coords);
    ctx.lineTo(...dest_coords);
    ctx.stroke();
    }
class hitbox {
    constructor(planet, west, north, east, south){
        this.planet = planet;
        this.west = west;
        this.north = north;
        this.east = east;
        this.south = south;
        }
    };

function getCanvasa()
{}
function draw_celestial(celestial){
    var phys_x, phys_y;
    var coords;
    var phys_radius = 0;
    coords = virt_to_phys(celestial.x, celestial.y);
    phys_x = Math.floor(coords[0]);
    phys_y = Math.floor(coords[1]);
    if (zoom_level < 1){
        phys_radius = Math.round(celestial.radius / (zoom_factor ** zoom_level * 1000000));
        console.log(phys_radius);
        }
    if (phys_radius <= 1){
        make_star(phys_x, phys_y, 43, celestial.color);
        }
    else {
        ctx.beginPath();
        ctx.arc(phys_x, phys_y, phys_radius, 0, 2*Math.PI);
        ctx.fillStyle = celestial.color;
        ctx.fill();
        }
    return [phys_x, phys_y]
}

function phys_to_virt(phys_x, phys_y){
    var x, y;
    x = (phys_x - (phys_width/2)) * (zoom_factor**zoom_level*1000000) + virt_x;
    y = (phys_y - (phys_height/2)) * (zoom_factor**zoom_level*1000000) + virt_y;
    return [x, y]
    }

function virt_to_phys(x, y){
    var new_x, new_y;
    new_x = (x - virt_x) / (zoom_factor ** zoom_level * 1000000) + (phys_width/2);
    new_y = (y - virt_y) / (zoom_factor ** zoom_level * 1000000) + (phys_height/2);
    return [new_x, new_y];
}

function create_stars() {
    var innerstring = starlist[1];
    innerstring += starlist[1][1];
    status_.innerHTML = innerstring;
    starlist.forEach(function (star){
        var celestial = new Celest(star[0], star[1], star[2], star[3], star[4], star[5], star[6]);
        allstars.push(celestial);
        var x_chunk = Math.floor(celestial.x/100000000000);
        var y_chunk = Math.floor(celestial.y/100000000000);
        if (x_chunk < 0){
            x_chunk = 0;
            }
        if (y_chunk < 0){
            y_chunk = 0;
            }
        chunks[x_chunk][y_chunk].push(celestial);
    });
}

var starlist;
var banana;// = 43;
var allstars = [];

socket.onmessage = function(event) {
    message = `[message] Data received from server: ${event.data}`;
    star_data = JSON.parse(event.data);
    starlist = star_data["ITEMS"];
    switch(star_data["MESSAGE_TYPE"]){
        case "STAR_LIST":
        {
            create_stars();
            //redraw();
            break;
            }
        case "SHIPMENT_ARRIVED": {
            break;
            }
        }
    };
socket.onclose = function(event) {
    if (event.wasClean) {
        alert(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
    } else {
        alert('[close] connection died');
    }
};

socket.onerror = function(error) {
    alert(`[error] ${error.message}`);
    };

var x, y;
var purple, blue, red, yellow, orange, red, white;
purple = [255, 255, 0];
var color_dict = {
    test:   [255,   128,0 ,        255],

    blue:   [  0,   0, 255,        255],
    green:  [  0, 255,   0,        255],
    teal:   [  0, 255, 255,        255],
    red:    [255,   0,   0,        255],
    purple: [255,   0, 255,        255],
    yellow: [255, 255,   0,        255],
    white:  [255, 255, 255,        255],
    orange: [255, 127,   0,        255],
}
function change_color(color){
    color = color_dict[color];
    d[0] = color[0];
    d[1] = color[1];
    d[2] = color[2];
    d[3] = color[3];

}
function make_star(x, y, i, color){
    ctx.fillStyle = color;
    change_color(color);
    ctx.putImageData(image_data, x, y);
    }

var x = 0;
var y = 0;
var number_of_stars = 5000;
var i = 0;
var image_data = ctx.createImageData(1, 1);
var d = image_data.data;
var html_tag;
function add(planet, z_l) {
    var element = document.createElement("button");
    element.value = name;
    element.name = name;
    element.innerHTML = planet.name;
    element.name = "banana";
    element.value = Number(z_l);
    element.onclick = function() {
        focused_celestial = planet;
        virt_x = planet.x;
        virt_y = planet.y;
        console.log(typeof(this.value));
        zoom_level = Number(this.value);
        //redraw();

        }
    var foo = document.getElementById("bookmarks");
    foo.appendChild(element);

    }
function create_planet_dropdown(celestial) {
    var source_planet_dropdown = document.getElementById("source_planet_dropdown");
        let x_chunk = Math.floor(celestial.x/100000000000)
        let y_chunk = Math.floor(celestial.y/100000000000)
        let this_chunk = chunks[x_chunk][y_chunk];
        let leftmost = Math.max(0, x_chunk-1);
        let rightmost = Math.min(99, x_chunk+1);
        let topmost = Math.max(0, y_chunk-1);
        let bottommost = Math.min(99, y_chunk+1);

        var neighboring_chunks = []
        let temp_x = leftmost;
        while (temp_x <= rightmost) {
            let temp_y = topmost;
            while (temp_y <= bottommost) {
                neighboring_chunks.push(chunks[temp_x][temp_y]);
                console.log(neighboring_chunks);
                temp_y++;
                }
            temp_x++;
            }
        let joined_array = [].concat(...neighboring_chunks);
        joined_array.sort(distance_squared);
        joined_array.forEach(function(celestial2){
            celestial2.option_element.innerHTML = celestial2.x + " " + celestial2.name + distance_squared(celestial, celestial2);
            source_planet_dropdown.appendChild(celestial2.option_element);
            });
    }

function distance_squared(a, b) {
    console.log(focused_celestial, a, b, focused_celestial.x, focused_celestial.y, a.x, b.x);
    a_distance = (focused_celestial.x - a.x)**2 + (focused_celestial.y - a.y)**2
    b_distance = (focused_celestial.x - b.x)**2 + (focused_celestial.y - b.y)**2
    if (a_distance >= b_distance) {
        return 1;
        } else {
        return -1;
        }
    return a_distance > b_distance ? -1 : 1;
    }

function remake_bookmarks() {
    var bookmarks_html = "";
    bookmarks.forEach(function(bookmark){
        bookmarks_html += ("<button class='bookmark' onclick='bookmark_button_press()'>" + bookmark[0].name + "</button>");
        });
    html_tag.innerHTML = bookmarks_html;
    }
function replacer(key, value) {
    if (["source_obj", "destination_obj"].includes(key)) {
        return value;
        //TODO: worry about this later.
        return undefined
        };
    return value

    }
class Shipment {
    constructor(source_id, dest_id, manifest) {
        this.source = source_id;
        this.destination = dest_id;
        this.manifest = manifest;
        this.message_type = "ship";
        var source_obj;
        var destination_obj;
        var current_coords;
        this.approved = true;
        this.distance = 0;
        this.speed = 100
        
        for (var i=0; i< allstars.length; i++) {
            if (i <= 10) {
                }
            if (allstars[i].id == source_id) {
                this.source_obj = allstars[i];
                this.current_coords = [this.source_obj.x, this.source_obj.y];
                }
            if (allstars[i].id == dest_id) {
                this.destination_obj = allstars[i];
                }
            }

        }
    update() {
        let x = this.current_coords[0];
        let y = this.current_coords[1];
        console.log("the x is: ", x, " the y is: ", y);
        let dest_coords = [this.destination_obj.x, this.destination_obj.y];
        let source_coords = [this.source_obj.x, this.source_obj.y];
        let m = (dest_coords[1] - source_coords[1]) / (dest_coords[0] - source_coords[0]);
        let b = -1 * m * source_coords[0] + source_coords[1];
        var delta_x, delta_y;
        console.log("m is ", m, " b is ", b)
        console.log("speed: ", this.speed, " Math.sqrt(1+m**2)", Math.sqrt(1+m**2))
        if (dest_coords[0] >= source_coords[0]) {
            delta_x = x + this.speed / Math.sqrt(1+m**2);
            }
        else {
            delta_x = x - this.speed / Math.sqrt(1+m**2);
            }
        delta_y = m * delta_x + b;
        this.current_coords = [delta_x, delta_y];

        }
    toString = function(){
        return ["suource: ", this.source, "dest: ", this.destination];
        }

    }
function send_shipment_request() {
    // Send a shipment request to the server.
    socket.send("test");
//    var shipment = {message_type: "ship", source: 1, destination: 2000, manifest: [4,5,6,7]};
    sh = new Shipment(1, 2000, [4,5,6,7]);
    active_shipments.push(sh);
    socket.send(JSON.stringify(sh, replacer));
    }
var current_time = 0;
function set_time() {
    status_.innerHTML = current_time;
    current_time++;
    
    if (current_time %10 == 0){
        active_shipments.forEach(function(shipment){
            shipment.update();
            redraw()
            });
        }

    }
window.onload = function() {
    redraw();
    html_tag = document.getElementById("bookmarks");
    setInterval(set_time, 100);
    }
