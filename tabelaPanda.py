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

# Increase cell width by 50% and centralize
data[0] = [f'{cell:^{int(len(cell) * 1.5)}}' for cell in data[0]]
for i in range(1, len(data) - 2):
    data[i] = [f'{cell:^{int(len(cell) * 1.5)}}' if cell not in ("IGU", "SDU") else cell for cell in data[i]]

table_str = tabulate(data, tablefmt="plain")
font_size = 20
font_path = "/Library/Fonts/Arial.ttf"  # Change this to the correct path on your system
font = ImageFont.truetype(font_path, font_size)

cell_widths = [max(font.getbbox(cell)[2] for cell in column) for column in zip(*data)]
cell_height = font.getbbox(table_str.splitlines()[0])[3] + 10  # Adding padding

table_width = sum(cell_widths)
table_height = cell_height * len(data)

image = Image.new("RGBA", (table_width, table_height), (255, 255, 255, 255))
draw = ImageDraw.Draw(image)

y_position = 0
for i, row in enumerate(data):
    x_position = 0
    for j, cell in enumerate(row):
        color = "black"
        if cell == "IGU":
            color = "darkblue"
        elif cell == "SDU":
            color = "darkred"
        alignment = "center"
        if i == 0 or i == len(data) - 1 or i == len(data) - 2:
            alignment = "center"
        bbox = draw.textbbox((x_position, y_position), cell, font=font, align=alignment)
        x_offset = (cell_widths[j] - (bbox[2] - bbox[0])) // 2
        y_offset = (cell_height - (bbox[3] - bbox[1])) // 2
        draw.text((x_position + x_offset, y_position + y_offset), cell, fill=color, font=font, align=alignment)
        x_position += cell_widths[j]
    y_position += cell_height

# Desenhar linhas horizontais
for i in range(len(data) + 1):
    y = i * cell_height
    draw.line((0, y, table_width, y), fill="black", width=1)

# Desenhar linhas verticais
x_position = 0
for width in cell_widths:
    draw.line((x_position, 0, x_position, table_height), fill="black", width=1)
    x_position += width

image.save("styled_table.png")
image.show()
