# Valentine's Day Ticketing System

### Disclaimer
This was made in 2022. Links may have broken or changed. Information may be outdated.

## Tutorial for Prefects

### Overview of System
1. Prefects load the student timetables into the website.
2. Prefects generate codes for tickets using the website.
3. Prefects physically sell the codes to students.
4. Students visit the website to redeem the code. They generate a ticket by choosing a recipient and period (if special serenade), and writing a message (digital handwriting or typed). 
5. The website automatically sorts the tickets and assigns them into a group.
6. The website generates PDFs of the tickets for each group.
7. Prefects cut out the tickets from the PDFs and give them to the corresponding group.
8. On Valentine's Day, the delivery groups distribute the items and do the serenades!

### Step 1: Load the timetables of each year level
1. Ask a teacher to go on OneSchool and download the PDF timetables for each year level (and also teachers if necessary).
2. Convert PDFs to Excel files (using Adobe Acrobat is recommended).
3. Convert Excel files into CSV files.
4. Go to [timetables](https://statehigh.pythonanywhere.com/timetables/) and upload the CSV files.
5. Refresh the website.

### Step 2: Create and Sell Ticket Codes
1. Go the [admin](https://statehigh.pythonanywhere.com/admin/ticketing/ticketcodepdf/) and create a new TicketPDF object (pick the item type and the number of codes you want for that item).
2. Ensure you pick an appropriate number of ticket codes to generate for each item (in 2022, there were ~800 chocolates, ~1500 roses, ~400 serenades, ~120 special serenades).
3. You should be redirected to a page of a PDF.
4. Print out all the PDFs and cut them out.
5. Repeat this for all item types (Chocolate, Rose, Serenade, Special Serenades)
6. Sell the individual ticket codes to the students.

### Step 3: Redeem Tickets (this step is for students not prefects)
1. Buy a ticket code from the prefects for the item type that you want (e.g. if you want a serenade, buy a serenade code).
2. Go to [redeem](https://statehigh.pythonanywhere.com/redeem/) and enter your code.
3. If it's a special serenade, pick which period you want it in.
4. Find the recipient you want from the list.
5. Choose whether to handwrite or type your message.
6. In either case, pick which template you want to use.
7. If handwriting, just handwrite on the screen (Apple pens should work).
8. If typing, edit the "Placeholder" text on the template. You can resize and drag them around (but can't create more). To delete them, just remove all the text.
9. Press the redeem button!

### Step 4: Sort the Tickets
1. Optional: visit the [stats](https://statehigh.pythonanywhere.com/stats/) page to find out how many tickets have been created.
2. Go to [admin](https://statehigh.pythonanywhere.com/admin/ticketing/sortticketsrequest/) and create a TicketSortRequest object (with the settings you want). 
3. The website will automatically pick the optimal period for each ticket to be delivered in, and will distribute the tickets to each delivery group (i.e. the groups of serenaders and prefects who hand out the roses/chocolates).
4. You should be redirected to page listing all the delivery groups.
5. Here you generate the PDF for each group.
6. Download the PDFs for each group and print them all out (IMPORTANT: make sure to print double-sided flipped along the **horizontal** edge).
7. Cut them out and assign them to the corresponding delivery group (Recommended: when cutting out the tickets, cut along the long vertical line in the middle first, then the smaller horizontal ones so that the order is maintained).

### Step 5: Valentine's Day has arrived!
Now it's time to deliver the tickets! Here are some things to know:
- On the back of each ticket are 4 periods. The period with the symbol next to it is the chosen period. The tickets are ordered and grouped based on the chosen period, so it's optimal to deliver them according to the chosen period. The other 3 periods are added just in case something goes wrong (e.g. you don't have time to deliver all of them) and you need to deliver them later/earlier.
- On the bottom-left of each ticket is a code. 
  - The first character is a letter. It is either S or N (corresponding to whether the tickets are for a serenading delivery group, or a non-serenading delivery group, respectively).
  - After the letter is a number. This is the group number of the delivery group.
  - After that is a colon, then another number. This number is the ticket number of the delivery group.
  - For example, if the bottom-left of the ticket says *N2: 10*, then it is the 10th ticket of the 2nd non-serenading delivery group.

## Extra Technical Stuff

### Hosting
This website is currently hosted for free on a server provided by [pythonanywhere](https://www.pythonanywhere.com). Since it's free, it probably isn't very good and may be extremely slow or unresponsive. You may need to pay money and [upgrade to a better tier](https://www.pythonanywhere.com/user/statehigh/account/). In this case, you should pick the custom tier. Here's what matters and doesn't matter:

- CPU Time: doesn't matter because almost nothing will use this up. Pick the lowest possible (2000s).
- Number of Web Apps: doesn't matter because there's only one website (this one). Pick the lowest possible (1).
- Number of Web Workers: important. Increasing the number should make the website more responsive. Pick a reasonable number (2-4).
- Number of Always-on Tasks: doesn't matter because this website doesn't use any. Pick the lowest possible (1).
- Disk Space: important. It is vital that there is enough space to store all the tickets. Pick as low as you are willing to risk (2GB should be ok but 5GB if you want to be safe. 1GB might even be enough but I wouldn't risk it).

You only need to pay for this while you are using the website (i.e. from the start of school to Valentine's Day, which is about 1 month), so it shouldn't be very expensive at all (just take it out of the budget lol).

If you decide to stick with the free plan, you must remember to [activate the website](https://www.pythonanywhere.com/user/statehigh/webapps/#tab_id_statehigh_pythonanywhere_com) (it automatically disables itself after 3 months unless renewed). This is free to do but you can't forget.

In case of a last resort, you may need to change to a completely different hosting service. It will be a pain to configure the whole website again, so good luck.

### Backups
It is extremely important that you backup the database of this website. Navigate to the [website working directory](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day) and look for the file named *db.sqlite3*. This is the most important file in the whole website. If you lose this, you lose all the tickets; all the students who paid for a code will be very sad that they paid for nothing. If everything else breaks but this file is intact, the operation is still salvagable. **I recommend you backup this file everyday**, with a separate file for each day (don't just override and only keep yesterday's copy).

## Forgot Password?
If you lose the password to the pythonanywhere account, you will have to contact me so I can reset it (it's linked to my email). Try not to do this.

If you lose the password to the website but have access to the pythonanywhere account, then it's not too hard to fix. Open a new Bash console and navigate to the working directory (*home/statehigh/valentines-day*). Then type the command *python manage.py createsuperuser*. This will prompt you to create a new admin account for the website.


### Libraries Used
These are the libraries that this website uses. You shouldn't need to worry because the libraries are pre-installed on pythonanywhere and I already installed the fonts. If you decide to add fonts, you will have to install these to the pythonanywhere instance. [Here's](https://help.pythonanywhere.com/pages/Fonts/) a tutorial on how to install fonts. If you use a version newer than the one stated (e.g. Python 3.10), then there is a chance that this website will break if the newer version depreciated some features that this website uses (quite unlikely to happen anytime soon).
- Python 3.8+
- Django 4.0+
- ReportLab 3.6+
- CairoSVG 2.5+
- lxml 4.9+
- Intall custom fonts found in [the fonts folder](ticketing/static/fonts) into the OS font library.
