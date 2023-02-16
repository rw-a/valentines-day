/* Loading Template */
function load_background_image(template_src) {
    return new Promise((resolve) => {
        fabric.Image.fromURL(template_src, (img) => {
            fabric_canvas.setBackgroundImage(img, () => {
                fabric_canvas.renderAll.bind(fabric_canvas);
                resolve();
            }, {
                scaleX: fabric_canvas.width / img.width,
                scaleY: fabric_canvas.height / img.height
            });
        });
    })
}

async function initialise_template() {
    fabric_canvas.clear();

    let template = document.getElementById('typed_template').value;
    if (template === "Blank") {
        const texts = [
            new fabric.IText('Placeholder', {"left": 18, "top": 20, "fontSize": 30}),
            new fabric.IText('Placeholder', {"left": 18, "top": 120, "fontSize": 30}),
            new fabric.IText('Placeholder', {"left": 18, "top": 220, "fontSize": 30})
        ];
        fabric_canvas.add(...texts);
    } else if (Object.keys(templates).includes(template)) {
        const filename = (templates[template].filenameRedeem) ? templates[template].filenameRedeem : templates[template].filename;
        const filePath = `${static_path}templates/${filename}`;
        await load_background_image(filePath);
        let texts = [];
        for (let text_info of templates[template].textPosition) {
            texts.push(new fabric.IText('Placeholder', text_info));
        }
        fabric_canvas.add(...texts);
    } else {
        console.error(`Template ${template} not found.`);
    }
    await load_font();
}

document.getElementById('typed_template').addEventListener('change', async (event) => {
    await initialise_template();
});


/* Undo, Reset & Clear */
let fabric_canvas_data;
let undo_history = [];

function save_fabric() {    // saves the canvas state into undo history
    if (fabric_canvas_data) {
        undo_history.push(fabric_canvas_data);
    }
    fabric_canvas_data = JSON.stringify(fabric_canvas);
}

// reset button
document.getElementById("fabric_reset").addEventListener("click", async () => {
    document.getElementById('tooManyTextBoxesError').hidden = true;
    await initialise_template();
});

// clear button
document.getElementById("fabric_clear").addEventListener("click", () => {
    document.getElementById('tooManyTextBoxesError').hidden = true;
    fabric_canvas.remove(...fabric_canvas.getObjects());  // delete all objects but not background
    save_fabric();
});

// undo button
document.getElementById("fabric_undo").addEventListener("click", (event) => {
    document.getElementById('tooManyTextBoxesError').hidden = true;
    if (undo_history.length > 0) {
        fabric_canvas_data = undo_history.pop();
        event.target.disabled = true;
        fabric_canvas.clear();
        fabric_canvas.loadFromJSON(fabric_canvas_data, () => {
            fabric_canvas.renderAll();
            document.getElementById('font_selector').value = fabric_canvas.item(0).fontFamily;;
            event.target.disabled = false;
        });
    }
});

/* Init */
const fabric_canvas = new fabric.Canvas('fabric');

fabric_canvas.on('object:modified', function() {
    save_fabric();
});

/* Load Fonts */
async function load_font() {
    const font = document.getElementById("font_selector").value;
    let myFont = new FontFaceObserver(font);
    await myFont.load();
    fabric_canvas.getObjects().forEach((object) => {object.set("fontFamily", font);})
    fabric_canvas.requestRenderAll();
    save_fabric();
}

const font_selector = document.getElementById("font_selector");
const fontStyles = document.createElement('style');
for (let font of Object.keys(fonts)) {
    const option = document.createElement('option');
    option.innerHTML = font;
    option.value = font;
    font_selector.appendChild(option);

    const fontFilename = fonts[font];
    let format;
    if (fontFilename.endsWith("woff2")) {
        format = "format('woff2')"
    } else if (fontFilename.endsWith("woff")) {
        format = "format('woff')"
    }
    fontStyles.appendChild(document.createTextNode(`\
        @font-face {\
            font-family: '${font}';\
            src: url('${static_path}fonts/${fontFilename}') ${format};\
        }\
    `));
}
document.head.appendChild(fontStyles);

font_selector.onchange = async function() {
    await load_font();
}

initialise_template();

/* Delete text box button */
const deleteImg = document.createElement('img');
deleteImg.src = `${static_path}icons/cancel.svg`;
function renderIcon(icon) {
    return function renderIcon(ctx, left, top, styleOverride, fabricObject) {
      let size = this.cornerSize;
      ctx.save();
      ctx.translate(left, top);
      ctx.rotate(fabric.util.degreesToRadians(fabricObject.angle));
      ctx.drawImage(icon, -size/2, -size/2, size, size);
      ctx.restore();
    }
}

function deleteObject(eventData, transform) {
    let target = transform.target;
    let canvas = target.canvas;
    canvas.remove(target);
    canvas.requestRenderAll();
    document.getElementById('tooManyTextBoxesError').hidden = true;
    save_fabric();
}

fabric.Object.prototype.controls.deleteControl = new fabric.Control({
    x: 0.5,
    y: -0.5,
    offsetY: -16,
    offsetX: 16,
    cursorStyle: 'pointer',
    mouseUpHandler: deleteObject,
    render: renderIcon(deleteImg),
    cornerSize: 20
});

/* Add text box button */
document.getElementById('fabric_add').addEventListener('click', () => {
    const objects = fabric_canvas.getObjects();
    if (objects.length >= 10) {
        document.getElementById('tooManyTextBoxesError').hidden = false;
        return;
    }

    // default coordinates to place new text boxes
    const left_default = 400;
    const top_default = 20;
    let left = left_default;
    let top = top_default;

    // determine a place which is free
    let spaceAvailable = false;
    while (!spaceAvailable) {
        spaceAvailable = true;
        for (let object of objects) {
            if (object.left === left && object.top === top) {
                spaceAvailable = false;
                top += 40;
                if (top > 300) {
                    // if not enough vertical space, move left and restart
                    left -= 40;
                    top = top_default;
                    if (left <= 20) {
                        // if entire board is full, restart entirely
                        left = left_default;
                    }
                }
                break;
            }
        }
    }

    fabric_canvas.add(new fabric.IText('Placeholder', {"left": left, "top": top, "fontSize": 30, "fontFamily": document.getElementById("font_selector").value}));
    save_fabric();
});