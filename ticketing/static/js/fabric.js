/* Loading Template */
function load_background_image(template_src, default_font) {
    fabric_canvas.clear();

    fabric.Image.fromURL(template_src, function(img) {
        fabric_canvas.setBackgroundImage(img, fabric_canvas.renderAll.bind(fabric_canvas), {
            scaleX: fabric_canvas.width / img.width,
            scaleY: fabric_canvas.height / img.height
        });
        load_font(default_font);
    });
}

function initialise_template() {
    let template = document.getElementById('id_typed_template').value;
    if (Object.keys(templates).includes(template)) {
        load_background_image(`${static_path}templates/${templates[template].filename}`, templates[template].defaultfont);
        let texts = [];
        for (let text_info of templates[template].textposition) {
            texts.push(new fabric.IText('Placeholder', text_info));
        }
        fabric_canvas.add(...texts);
    } else {
        console.error(`Template ${template} not found.`);
    }
}

document.getElementById('id_typed_template').addEventListener('change', (event) => {
    initialise_template();
})


/* Undo & Clear */
let fabric_canvas_data;
let undo_history = [];

function save_fabric() {       // this should not be called by itself. only called by load font and event listeners
                               // initial call won't have a state
    if (fabric_canvas_data) {
        undo_history.push(fabric_canvas_data);
        document.getElementById('fabric_undo').disabled = false;
    }
    fabric_canvas_data = JSON.stringify(fabric_canvas);
}

// clear button
document.getElementById("fabric_clear").addEventListener("click", () => {
    initialise_template();
});

// undo button
document.getElementById("fabric_undo").addEventListener("click", () => {
    if (undo_history.length > 0) {
        fabric_canvas_data = undo_history.pop();
        this.disabled = true;
        fabric_canvas.clear();
        fabric_canvas.loadFromJSON(fabric_canvas_data, function() {
            fabric_canvas.renderAll();
            this.disabled = false;
        });
    }
});

/* Init */
const fabric_canvas = new fabric.Canvas('fabric');

fabric_canvas.on('object:modified', function() {
    save_fabric();
});

/* Load Fonts */
function load_font(font) {
    if (font === undefined) {
        var font = document.getElementById("font_selector").value;
    }

    let myfont = new FontFaceObserver(font);
    myfont.load()
        .then(function() {
            fabric_canvas.getObjects().forEach(function(object) {object.set("fontFamily", font);})
            fabric_canvas.requestRenderAll();
            save_fabric();
        }).catch(function(e) {
            console.log(e);
            alert('Failed to load font: ' + font);
    });
}

let fonts = ["Calibri", "Chasing Hearts", "Delique", "Heartales", "Hello Valentine", "La Rosse", "Love Letters", "Roschetta"];
let font_selector = document.getElementById("font_selector");
fonts.forEach(function(font) {
    let option = document.createElement('option');
    option.innerHTML = font;
    option.value = font;
    font_selector.appendChild(option);
});

font_selector.onchange = function() {
    load_font();
}

initialise_template();