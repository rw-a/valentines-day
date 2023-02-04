# Customising the Tickets
If you make a mistake, it's usually quite easy to revert back to a previous state. If you need to do so, please contact me. If you successfully make any changes, also please contact me so that I can save them - that way, if someone else down the line wants to make changes, they can revert back to the changes you made (so all the progress you made isn't wasted).

If you want to make changes but this is too difficult to follow, feel free to ask me and I can help.

## Adding/Changing Pickup Lines
The pickup lines are stored at [*ticketing/static/pickup_lines.txt*](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day/static/pickup_lines.txt?edit). Each new line in the text file corresponds to a different pickup line. If you are adding new pickup lines, simply add each one to a new line. Ensure that they aren't too long or else they may cause weird formatting when printed. To remove pickup lines, simply delete the entire line in the text file. Ensure that there are no empty rows (check the last line in particular for a sneaky blank row), or else some tickets may be blank.

Once you have made your changes, go to the [pythonanywhere dashboard](https://www.pythonanywhere.com/user/statehigh/) and press the *$Bash* button below the *New console* heading. Then type the following into the bash console:
```
cd valentines-day/
python manage.py collectstatic
yes
```
Finally, you need to reload the website. Go to the [webapp on pythonanywhere](https://www.pythonanywhere.com/user/statehigh/webapps/) and press the reload button.

## Adding/Changing Fonts
1. Download the font you want as a .tff file.
2. Add the file to [*ticketing/static/fonts/*](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day/ticketing/static/fonts).
3. Install the font into the server by following [this tutorial](https://help.pythonanywhere.com/pages/Fonts/).
4. Open [*ticketing/static/css/redeem.css*](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day/ticketing/static/css/redeem.css?edit) and register the font file by adding the following piece of code somewhere. Note that font-family is the name of the font is, and src is the name of the file (spaces need to have a backslash before them, as shown).

```
@font-face {
    font-family: "New Font";
    src: url("../fonts/New\ Font.ttf");
}
```

5. Open [*ticketing/static/js/fabric.js*](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day/static/js/fabric.js?edit). Locate the variable that is an array of fonts, and add your new font to the list (the name that you chose for font-family, not the filename).

```
...
let fonts = ["Calibri", "Chasing Hearts", "Delique", "Heartales", "Hello Valentine", "La Rosse", "Love Letters", "Roschetta", "New Font"];
...
```

6. Reload the website by going to the [webapp on pythonanywhere](https://www.pythonanywhere.com/user/statehigh/webapps/) and pressing the green reload button.

## Adding/Changing Ticket Templates
1. Download [this Word document](https://github.com/rw-a/valentines-day/blob/master/Classic%20Template.docx), which was used to create the classic template.
2. Modify the template to create your own! Note: It's very important that you don't change the size of each cell in the table (actually, the size isn't critical but the width must be exactly 1.68x longer than the height).
3. Export the Word document as a PDF.
4. Convert the PDF into an SVG file using [Inkscape](https://inkscape.org/).
5. Add the SVG file to the templates folder, which is located at [*ticketing/static/templates/*](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day/ticketing/static/templates).
6. Open [*ticketing/static/templates/templates.json*](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day/ticketing/static/templates/templates.json?edit) and register your new template in the file. Make sure you follow the exact conventions. Here's an example:

```
{
  "Classic Template": {
    "filename": "classic_template.svg",
    "defaultfont": "Calibri",
    "textposition": [
        {"left": 18, "top": 60, "fontSize": 30},
        {"left": 170, "top": 164, "fontSize": 30},
        {"left": 102, "top": 212, "fontSize": 30},
        {"left": 102, "top": 260, "fontSize": 30},
        {"left": 157, "top": 308, "fontSize": 30}
    ]
  },
    "Modern Template": {
    "filename": "modern_template.svg",
    "defaultfont": "Roboto",
    "textposition": [
        {"left": 28, "top": 30, "fontSize": 25},
        {"left": 183, "top": 112, "fontSize": 25},
        {"left": 125, "top": 85, "fontSize": 25},
        {"left": 173, "top": 225, "fontSize": 30},
        {"left": 125, "top": 275, "fontSize": 30}
    ]
  }
}
```

7. If you set a default font which isn't in the existing list, you will also need to register it. [See above](https://github.com/rw-a/valentines-day/blob/master/Customisation.md#addingchanging-fonts)
8. Reload the website by going to the [webapp on pythonanywhere](https://www.pythonanywhere.com/user/statehigh/webapps/) and pressing the green reload button.
