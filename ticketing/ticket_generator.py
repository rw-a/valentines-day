import cairosvg
import io
import PIL
import random
from lxml import etree
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak, Paragraph
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus.tables import Table, TableStyle
from constants import DirectoryLocations
# from .ticket_sorter import TicketToSort


class TicketsToPDF:
    def __init__(self, tickets: list,  pdf_output_name: str):
        self.tickets = tickets
        self.pdf_output_name = pdf_output_name

        """Constants and Settings"""
        self.NUM_COLUMNS = 2
        self.NUM_ROWS = 5
        self.NUM_CODES_PER_PAGE = self.NUM_COLUMNS * self.NUM_ROWS

        self.MARGIN = 1 * cm      # an additional 0.5cm will be added to the table
        self.PADDING = 0          # the padding for each cell in the table
        self.PAGE_WIDTH, self.PAGE_HEIGHT = A4

        self.TABLE_WIDTH = self.PAGE_WIDTH - 2 * self.MARGIN - cm
        self.TABLE_HEIGHT = self.PAGE_HEIGHT - 2 * self.MARGIN - cm
        self.CELL_WIDTH = self.TABLE_WIDTH / self.NUM_COLUMNS
        self.CELL_HEIGHT = self.TABLE_HEIGHT / self.NUM_ROWS

        self.ITEM_TYPE_IMAGE_SIZE = 40      # in pts

        # dimensions of canvas from signature pad in pixels
        self.CANVAS_WIDTH = 602
        self.CANVAS_HEIGHT = 358
        self.RATIO = 2      # increases DPI by this ratio

        """Templates"""
        self.CLASSIC_TEMPLATE = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
            url="ticketing/static/classic_template.svg", write_to=None,
            output_width=self.CANVAS_WIDTH * self.RATIO, output_height=self.CANVAS_HEIGHT * self.RATIO)))

        self.generate_pdf()

    def generate_pdf(self):
        doc = SimpleDocTemplate(self.pdf_output_name, pageSize=A4,
                                rightMargin=self.MARGIN, leftMargin=self.MARGIN,
                                topMargin=self.MARGIN, bottomMargin=self.MARGIN)

        # split the list into pages
        pages = []
        for tickets in self.split_list(self.tickets, self.NUM_CODES_PER_PAGE):     # for each page of codes
            """Front of tickets"""
            # split the list again into rows
            data = self.split_list(self.create_images(tickets), self.NUM_COLUMNS)
            pages.append(self.create_table(data))

            pages.append(PageBreak())

            """Back of tickets"""
            data = self.split_list(self.create_delivery_info(tickets), self.NUM_COLUMNS)
            pages.append(self.create_table(data))
        doc.build(pages)

    def create_images(self, tickets: list) -> list:
        images = []
        for ticket in tickets:
            # resize the canvas
            with open(f"{DirectoryLocations().REDEEMED_TICKETS}/{ticket.id}.svg") as file:
                xml_file = etree.parse(file).getroot()
                # change the view box to the dimensions of the canvas
                xml_file.set('viewBox', f'0 0 {self.CANVAS_WIDTH} {self.CANVAS_HEIGHT}')

            # add the template if required
            if ticket.template > 0:
                handwritten_image = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
                    bytestring=etree.tostring(xml_file), write_to=None,
                    output_width=self.CANVAS_WIDTH * self.RATIO, output_height=self.CANVAS_HEIGHT * self.RATIO)))
                combined_image = PIL.Image.new(
                    'RGBA', (handwritten_image.width, handwritten_image.height), (255, 255, 255, 0))

                if ticket.template == 1:
                    combined_image.alpha_composite(self.CLASSIC_TEMPLATE)
                else:
                    raise KeyError(f"Template number {ticket.template} does not exist.")

                combined_image.alpha_composite(handwritten_image)

                # save as bytes
                img_bytes = io.BytesIO()
                combined_image.save(img_bytes, format='PNG')
            else:
                img_bytes = io.BytesIO(cairosvg.svg2png(bytestring=etree.tostring(xml_file), write_to=None))

            image = Image(img_bytes)
            self.scale_image(image, self.CELL_WIDTH - 2 * self.PADDING, self.CELL_HEIGHT - 2 * self.PADDING)

            images.append(image)
        return images

    def create_delivery_info(self, tickets: list) -> list:
        stylesheet = getSampleStyleSheet()
        default_style = ParagraphStyle(name="Default", parent=stylesheet['Normal'], fontSize=14)
        left_align = ParagraphStyle(name="Left", parent=default_style, alignment=0, leftIndent=1)
        right_align = ParagraphStyle(name="Right", parent=default_style, alignment=2, rightIndent=1)
        centre_align = ParagraphStyle(name="Centre", parent=default_style, alignment=1)
        large_style = ParagraphStyle(name="Large", parent=default_style, alignment=1, fontSize=16, leading=16)

        ticket_backs = []
        for ticket in tickets:
            """Left Side: Periods"""
            p1 = [Paragraph("P1: ", right_align), Paragraph(ticket.p1, left_align)] if not ticket.is_p1 else \
                [Paragraph("<b>P1: </b>", right_align), Paragraph(f"<b>{ticket.p1}</b>", left_align)]
            p2 = [Paragraph("P2: ", right_align), Paragraph(ticket.p2, left_align)] if not ticket.is_p2 else \
                [Paragraph("<b>P2: </b>", right_align), Paragraph(f"<b>{ticket.p2}</b>", left_align)]
            p3 = [Paragraph("P3: ", right_align), Paragraph(ticket.p3, left_align)] if not ticket.is_p3 else \
                [Paragraph("<b>P3: </b>", right_align), Paragraph(f"<b>{ticket.p3}</b>", left_align)]
            p4 = [Paragraph("P4: ", right_align), Paragraph(ticket.p4, left_align)] if not ticket.is_p4 else \
                [Paragraph("<b>P4: </b>", right_align), Paragraph(f"<b>{ticket.p4}</b>", left_align)]
            period_data = [p1, p2, p3, p4]
            period_table = self.create_div(period_data, ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                           colWidths=self.CELL_WIDTH / 6, rowHeights=self.CELL_HEIGHT / 7)

            """Right Side: Item Type (including image)"""
            if ticket.item_type == "Chocolate":
                item_type_image = self.scale_image(Image('ticketing/static/item_types/chocolate.png'),
                                                   self.ITEM_TYPE_IMAGE_SIZE, self.ITEM_TYPE_IMAGE_SIZE)
            elif ticket.item_type == "Rose":
                item_type_image = self.scale_image(Image('ticketing/static/item_types/rose.png'),
                                                   self.ITEM_TYPE_IMAGE_SIZE, self.ITEM_TYPE_IMAGE_SIZE)
            elif ticket.item_type == "Serenade":
                item_type_image = self.scale_image(Image('ticketing/static/item_types/serenade.png'),
                                                   self.ITEM_TYPE_IMAGE_SIZE, self.ITEM_TYPE_IMAGE_SIZE)
            elif ticket.item_type == "Special Serenade":
                item_type_image = self.scale_image(Image('ticketing/static/item_types/special_serenade.png'),
                                                   self.ITEM_TYPE_IMAGE_SIZE, self.ITEM_TYPE_IMAGE_SIZE)
            else:
                raise KeyError("Unknown item type")

            item_type = Paragraph(ticket.item_type, centre_align)
            item_type_and_period = [[item_type_image], [item_type]]
            item_type_and_period_table = self.create_div(item_type_and_period)

            left_right_side = [[period_table, item_type_and_period_table]]
            left_right_table = self.create_div(left_right_side,
                                               ('VALIGN', (0, 0), (-1, -1), 'CENTER'), colWidths=self.CELL_WIDTH / 2)

            """Top Side: Recipient Name"""
            top_bottom = [[Paragraph(f"{ticket.recipient_name} <br/>", large_style)], [left_right_table]]
            name_height = 40 if len(ticket.recipient_name) <= 30 else 50
            top_bottom_table = self.create_div(top_bottom, ('VALIGN', (0, 0), (-1, -1), 'CENTER'),
                                               rowHeights=[name_height, None])

            ticket_backs.append(top_bottom_table)
        return ticket_backs

    @staticmethod
    def split_list(ticket_codes: list, split_size: int) -> list:
        # splits a list into smaller lists of a given size
        return [ticket_codes[i: i + split_size] for i in range(0, len(ticket_codes), split_size)]

    @staticmethod
    def scale_image(image: Image, width: float, height: float = None) -> Image:
        # scale image to desired dimensions (in pts)
        # scale using the smallest amount (out of width or height) so that it fits while preserving aspect ratio
        if height is None:
            height = width
        scale_width = width / image.drawWidth
        scale_height = height / image.drawHeight
        scale = min(scale_width, scale_height)
        image.drawWidth *= scale
        image.drawHeight *= scale
        return image

    def create_table(self, data: list) -> Table:
        table = Table(data, colWidths=self.CELL_WIDTH, rowHeights=self.CELL_HEIGHT)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
        ]))
        return table

    @staticmethod
    def create_div(data: list, *table_styles, **kwargs) -> Table:
        table = Table(data, **kwargs)
        table.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                # ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                # ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                *table_styles
            ]))
        return table


def main():
    from glob import glob

    class Ticket:
        def __init__(self, id, template: int):
            self.id = id
            self.template = template

            self.item_type = random.choice(["Chocolate", "Rose", "Serenade", "Special Serenade"])
            self.recipient_name = "Senugi Dissan Mudiyanselage"

            self.p1 = "F101"
            self.p2 = "F202"
            self.p3 = "F303"
            self.p4 = "F404"

            # whether the algorithm has chosen this period. don't rename or else setattr() will break
            self.is_p1 = False
            self.is_p2 = True
            self.is_p3 = False
            self.is_p4 = False

            self.chosen_period = 2
            self.chosen_classroom = "F202"

    tickets = [Ticket(file.split("/")[-1].split(".svg")[0], 1) for file in glob(f"{DirectoryLocations().REDEEMED_TICKETS}/*.svg")]

    TicketsToPDF(tickets, 'export.pdf')


if __name__ == "__main__":
    main()
