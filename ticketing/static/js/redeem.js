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