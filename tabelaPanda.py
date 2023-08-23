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

# Increase cell width by 50%
data[0] = [f'{cell:^{int(len(cell) * 1.5)}}' for cell in data[0]]
for i in range(1, len(data)):
    data[i] = [f'{cell:^{int(len(cell) * 1.5)}}' if cell not in ("IGU", "SDU") else cell for cell in data[i]]

table_str = tabulate(data, headers="firstrow", tablefmt="plain")
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
for row in data:
    x_position = 0
    for cell, width in zip(row, cell_widths):
        color = "black"
        if cell == "IGU":
            color = "darkblue"
        elif cell == "SDU":
            color = "darkred"
        draw.text((x_position, y_position), cell, fill=color, font=font)
        x_position += width
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
