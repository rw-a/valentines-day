/* INPUT VALIDATION */
let is_special = false;
async function check_validity(event, code_validated = false) {
    // these are stored in variables first to prevent short-circuiting
    if (code_validated) {  // don't validate code if this was called from the is_valid_code function to prevent recursion
        var validate_code = true;
    } else {
        validate_code = await is_valid_code(null, true);
    }
    let validate_period = is_valid_period();
    let validate_recipient = is_valid_recipient();
    if (document.getElementById('id_is_handwritten').value === "True") {
        var validate_content = await is_valid_handwriting();
    } else {
        validate_content = is_valid_typed();
    }

    if (validate_code && validate_period && validate_recipient && validate_content) {
        document.querySelector('form').submit();
    }
}

// btw this is also verified in the backend
async function is_valid_code(event, submit = false) {
    document.getElementById('code-error').hidden = false;
    is_special = false;

    let inputted_code = document.getElementById('id_code').value;
    if (inputted_code.length === 10) {
        let response = await fetch(validate_code_url + "?" + new URLSearchParams({inputted_code}))
        let data = await response.json();
        if (data.is_exists) {
            if (data.is_unconsumed) {
                document.getElementById('code-error').innerText = data.item_type;
                document.getElementById('code-error').style.color = '#71d16d';
                if (data.item_type === "Special Serenade") is_special = true;
                show_period();
                if (submit) {
                    check_validity(null, code_validated = true);
                } else {
                    return true;
                }
            } else {
                document.getElementById('code-error').innerText = "Code has already been used.";
                document.getElementById('code-error').style.color = 'red';
                show_period();
                return false;
            }
        } else {
            document.getElementById('code-error').innerText = "Code doesn't exist.";
            document.getElementById('code-error').style.color = 'red';
            show_period();
            return false;
        }
    } else {
        document.getElementById('code-error').innerText = "Code must be exactly 10 characters long.";
        document.getElementById('code-error').style.color = 'red';
        show_period();
    }
}

function show_period() {
    document.getElementById('period-form').hidden = !is_special;
}

function is_valid_period() {
    if (is_special) {
        let period = document.getElementById('id_period').value;
        if (period >= 1 && period <= 4) {
            document.getElementById('period-error').hidden = true;
            return true;
        } else {
            document.getElementById('period-error').hidden = false;
            return false;
        }
    } else {
        return true;
    }
}

function is_valid_recipient() {
    // check if the user actually inputted someone
    let recipient = document.getElementById('id_recipient_id').value;
    if (recipient.length > 3) {
        document.getElementById('recipient-error').hidden = true;
        return true;
    } else {
        document.getElementById('recipient-error').hidden = false;
        return false;
    }
}

async function is_valid_handwriting() {
    if (signaturePad.isEmpty()) {
        document.getElementById('handwriting-error').hidden = false;
        return false;
    } else {
        document.getElementById('handwriting-error').hidden = true;
        document.getElementById('id_message').value = await dataURLToBlob(signaturePad.toDataURL("image/svg+xml")).text();
        return true;
    }
}

function is_valid_typed() {
    fabric_canvas.discardActiveObject();
    if (fabric_canvas_data.includes(`"text":"Placeholder"`)) {
        document.getElementById('typed_error').hidden = false;
        return false;
    } else {
        document.getElementById('typed_error').hidden = true;
        fabric_canvas.backgroundImage = null;
        document.getElementById('id_message').value = fabric_canvas.toSVG();
        return true;
    }
}

function dataURLToBlob(dataURL) {
  const parts = dataURL.split(';base64,');
  const contentType = parts[0].split(":")[1];
  const raw = window.atob(parts[1]);
  const rawLength = raw.length;
  const uInt8Array = new Uint8Array(rawLength);

  for (let i = 0; i < rawLength; ++i) {
    uInt8Array[i] = raw.charCodeAt(i);
  }

  return new Blob([uInt8Array], { type: contentType });
}

// only allow letters in code input and automatically make uppercase
document.getElementById('id_code').addEventListener('input', (event) => {
    let inputted_code = event.target.value;
    inputted_code = inputted_code.toUpperCase();
    inputted_code = inputted_code.replace(/[^a-z]/gi, '');
    event.target.value = inputted_code;
});

document.getElementById('id_code').addEventListener('input', is_valid_code);
document.getElementById('redeem').addEventListener('click', check_validity);

/* CHOOSING CONTENT MODE AND TEMPLATE*/
document.getElementById('id_is_handwritten').addEventListener('change', () => {
    if (event.target.value === "True") {
        document.getElementById('form_typed').hidden = true;
        document.getElementById('form_handwriting').hidden = false;
    } else {
        document.getElementById('form_typed').hidden = false;
        document.getElementById('form_handwriting').hidden = true;
    }
})

const choices = new Choices('#id_recipient_id', {
    placeholderValue: "Select a person...",
    searchPlaceholderValue: "Search for a person...",
    itemSelectText: '',
    renderChoiceLimit: 100,
    shouldSort: false,
    searchResultLimit: 10,
});

/* SIGNATURE PAD */
const wrapper = document.getElementById("form_handwriting");
const canvas = document.getElementById("signature_pad");
const signaturePad = new SignaturePad(canvas, {
  minDistance: 1,
  minWidth: 0.7,
  maxWidth: 1.5
});

let signaturePadData = {};
let signaturePadDataBackup = {};    // to allow you to undo clearing
signaturePad.addEventListener("endStroke", () => {
    signaturePadData = signaturePad.toData();
});

// scale canvas for retina display
function resizeCanvas() {
    const ratio = 5;
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    canvas.getContext("2d").scale(ratio, ratio);
    signaturePad.clear();
    if (Object.keys(signaturePadData).length) {
        signaturePad.fromData(signaturePadData);
    }
}
window.onresize = resizeCanvas;
resizeCanvas();

// clear button
document.getElementById("signature_pad_clear").addEventListener("click", () => {
    signaturePad.clear();
    if (Object.keys(signaturePadData).length) signaturePadDataBackup = signaturePadData;
    signaturePadData = {};
});

// undo button
document.getElementById("signature_pad_undo").addEventListener("click", () => {
    if (Object.keys(signaturePadData).length) {
        signaturePadData.pop(); // remove the last dot or line
        signaturePad.fromData(signaturePadData);
    } else if (Object.keys(signaturePadDataBackup).length) {
        signaturePad.fromData(signaturePadDataBackup);
    }
});

// choosing handwritten template
document.getElementById('id_handwriting_template').addEventListener('change', (event) => {
    let template = event.target.value;
        if (template === "0") {
            document.getElementById('signature_pad').style.background = "#fdfdfd";
        } else if (template === "1") {
            document.getElementById('signature_pad').style.background = `url("${classic_template_path}") 0% 0%/600px 356px`;
        }
})

/* FABRIC */

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

function initialise_classic_template() {
    load_background_image(classic_template_path, 'Calibri');
    let text1 = new fabric.IText('Placeholder', {left: 18, top: 60, fontSize: 30});
    let text2 = new fabric.IText('Placeholder', {left: 170, top: 164, fontSize: 30});
    let text3 = new fabric.IText('Placeholder', {left: 102, top: 212, fontSize: 30});
    let text4 = new fabric.IText('Placeholder', {left: 102, top: 260, fontSize: 30});
    let text5 = new fabric.IText('Placeholder', {left: 157, top: 308, fontSize: 30});
    fabric_canvas.add(text1, text2, text3, text4, text5);
}

function initialise_template() {
    let template = document.getElementById('id_typed_template').value;
    if (template === "1") {
        initialise_classic_template();
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
        document.getElementById('#fabric_undo').disabled = false;
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