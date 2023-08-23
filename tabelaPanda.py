from tabulate import tabulate
from PIL import Image, ImageDraw, ImageFont

data = [
    ["Companhia", "Saída", "Origem", "Chegada", "Destino"],
    ["LATAM", "9:50", "IGU", "12:25", "SDU"],
    ["LATAM", "9:50", "IGU", "13:20", "SDU"],
    ["AZUL", "9:55", "IGU", "13:55", "SDU"],
    ["AZUL", "11:05", "IGU", "16:20", "SDU"],
    ["GOL", "11:40", "IGU", "15:15", "SDU"],
    ["LATAM", "10:55", "SDU", "15:00", "IGU"],
    ["GOL", "10:30", "SDU", "14:40", "IGU"],
    ["AZUL", "8:00", "SDU", "14:15", "IGU"]
]

table_str = tabulate(data, headers="firstrow", tablefmt="grid")
font = ImageFont.load_default()

# Calculating the maximum width and height of cells
cell_width = max(font.getbbox(cell)[2] for row in data for cell in row)
cell_height = font.getbbox(table_str.splitlines()[0])[3]

table_width = cell_width * len(data[0])
table_height = cell_height * len(data)

image = Image.new("RGBA", (table_width, table_height), (255, 255, 255, 255))
draw = ImageDraw.Draw(image)
draw.text((0, 0), table_str, fill="black", font=font)

image.save("styled_table.png")
image.show()
