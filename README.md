# Valentine's Day Ticketing System

### Disclaimer
Made in 2022. Last updated February 2023. Links may have broken or changed. Information may be outdated.

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
1. Ask a teacher to go on OneSchool and download the PDF timetables for each year level (and also teachers if necessary). The timetable should look like one row per person and should be for a specific day.
2. Convert PDFs to Excel files. I recommend using Adobe Acrobat. If you don't have it, there's a free online version [here](https://www.adobe.com/au/acrobat/online/pdf-to-excel.html).
3. Convert Excel files into CSV files.
4. Go to [timetables](https://statehigh.pythonanywhere.com/timetables/) and upload the CSV files.
5. Reload the website by going to [pythonanywhere](https://www.pythonanywhere.com/user/statehigh/webapps/) and pressing the green reload button.

### Step 2: Create and Sell Ticket Codes
1. Go the [admin](https://statehigh.pythonanywhere.com/admin/ticketing/ticketcodepdf/) and create a new TicketPDF object (pick the item type and the number of codes you want for that item).
2. Ensure you pick an appropriate number of ticket codes to generate for each item (in 2022, there were ~800 chocolates, ~1500 roses, ~400 serenades, ~120 special serenades).
3. Note that only one ticket request can exist at a time. If you a second one, it will override the previous one (it won't be deleted but it might order the tickets incorrectly).
4. You should be redirected to a page of a PDF. (If you want to go back to this page, visit [the page you were on before](https://statehigh.pythonanywhere.com/admin/ticketing/ticketcodepdf/) and click on the link under the *url* heading of the ticket request.
5. Print out all the PDFs and cut them out.
6. Repeat this for all item types (Chocolate, Rose, Serenade, Special Serenades)
7. Sell the individual ticket codes to the students.

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
  - Recommended: this page shows you how many tickets have been assigned to each group. Usually, the serenading groups will have significantly more tickets than the non-serenading groups. You can delete the SortTicketRequest and make a new one with different settings to better suit how you want the tickets to be distributed. You may have to do this several times.
5. Here you generate the PDF for each group.
  - Warning: The PDFs can get very large (up to ~30MB each), so generating them all at once may exceed your storage quota. You can generate a few, print them, then delete them, then repeat for another few. To delete a PDF, go to the [delivery group admin page](https://statehigh.pythonanywhere.com/admin/ticketing/deliverygroup/). Select the group(s) whose PDF you would like to delete, and select the dropdown *Action* which has the *Go* button next to it. Select *Undo printing of...* and press the *Go* button. To check your storage quota, visit the [pythonanywhere dashboard](https://www.pythonanywhere.com/user/statehigh/).
6. Download the PDFs for each group and print them all out
  - **Important**: make sure to print double-sided flipped along the **horizontal** edge.
  - Recommended: print out only a few pages first to test whether your printer correctly aligns the front and back when printing double sided.
7. Cut them out and assign them to the corresponding delivery group (Recommended: when cutting out the tickets, cut along the long vertical line in the middle first, then the smaller horizontal ones so that the order is maintained).

### Step 5: Valentine's Day has arrived!
Now it's time to deliver the tickets! Here are some things to know:
- On the top-right of the back of each ticket are 4 periods. The period with the symbol next to it is the chosen period. The tickets are ordered and grouped based on the chosen period, so it's optimal to deliver them according to the chosen period. The other 3 periods are added just in case something goes wrong (e.g. you don't have time to deliver all of them) and you need to deliver them later/earlier.
- On the bottom-left of the back of each ticket is a code. 
  - The first character is a letter. It is either S or N (corresponding to whether the tickets are for a serenading delivery group, or a non-serenading delivery group, respectively).
  - After the letter is a number. This is the group number of the delivery group.
  - After that is a colon, then another number. This number is the ticket number of the delivery group.
  - For example, if the bottom-left of the ticket says *N2: 10*, then it is the 10th ticket of the 2nd non-serenading delivery group.
  
### Step 6: Cleaning up Valentine's Day
After Valentine's Day is over, you should clean up the website for next year. 
1. Go to the [admin](https://statehigh.pythonanywhere.com/admin) page and delete everything (i.e. every Ticket, TicketCodePDF, TicketCode, DeliveryGroup and SortTicketsRequest). You can do this by selecting all of them (then pressing another select all button which selects all across every page) and choosing the "Delete selected..." option the in dropdown, then pressing *Go*.
2. Go to [*redeemed_tickets* folder in pythonanywhere](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day/redeemed_tickets) and press the *Open Bash console here* button near the top-right of the page, next to the quota information. Then type the following into the console:
```
rm *.svg
```
Caution: this will delete all the tickets and there is no way to undo this. Only do this after Valentine's Day is over.

## Customising the Tickets
You can:
1. Add/change pickup lines
2. Add/change fonts
3. Add/change ticket templates (the background image with the premade text and spaces for writing)

If you want to do so, see [this tutorial](Customisation.md).

## Maintaining the Website

### Console Limite Reached?
If you tried to create a new console but it told you that your console limit has been reached, you need to delete your old consoles. Go to the [consoles](https://www.pythonanywhere.com/user/statehigh/consoles/) page and press the delete button next to the existing consoles (should look something like *Bash console 27277339*), which is under the *Your consoles* heading. Now you can make new consoles, so try again in whatever you were doing before.

### Backups
To make a backup, you need to backup two things:

#### The Database
Navigate to the [website working directory in pythonanywhere](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day) and download the file named *db.sqlite3*. This stores the list of ticket codes and purchases made.

#### The Ticket Messages
Navigate to the [*redeemed_tickets* folder in pythonanywhere](https://www.pythonanywhere.com/user/statehigh/files/home/statehigh/valentines-day/redeemed_tickets). There should be a list of .svg files (or it could be empty if nobody has redeemed a ticket yet). These .svg files are the handwritten/typed messages that people made when they redeemed a ticket. The name of the ticket is the corresponding ID in the database, so do not rename the .svg files.

Since it only seems possible to download files individually, you should zip them all into one file first.
1. Press the *Open Bash console here* button near the top-right of the page, next to the quota information.
2. Type the following into the console:

```
zip mybackupfile.zip *.svg
```

3. Go back to the page you were on before and download zip file you just created.
4. Delete the zip file.

### Forgot Password
If you lose the password to the pythonanywhere account, you will have to contact me so I can reset it (it's linked to my email). Try not to do this.

If you lose the password to the website but have access to the pythonanywhere account, then it's not too hard to fix. Follow these steps:

1. Go to the [pythonanywhere](https://www.pythonanywhere.com/user/statehigh/) and press the *$Bash* button below the *New console* heading. 
2. Type the following into the bash console:
```
cd valentines-day/
python manage.py createsuperuser
```
3. Follow the steps shown in the console.
