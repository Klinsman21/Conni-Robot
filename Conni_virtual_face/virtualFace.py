import tkinter as tk
import math
import random
from itertools import cycle


class EilikEyes(tk.Tk):
    def __init__(self):
        super().__init__()
        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()

        self.withdraw()

        self.title("Olhos do Eilik - Expressões Animadas")
        self.configure(bg="black")
        self.config(cursor='none')
        self.overrideredirect(True)  # Remove bordas e barra de título
        self.geometry("{0}x{1}+0+0".format(
            self.winfo_screenwidth(), self.winfo_screenheight()))

        # Tecla ESC para sair
        self.bind("<Escape>", lambda e: self.destroy())

        # Configurações dos olhos
        self.eye_color = "#45b7d1"  # Azul claro estilo Eilik
        self.pupil_color = "#0e2a47"  # Azul escuro
        self.highlight_color = "white"
        self.eye_width = int(self.screen_w * 0.16)  # 8% da largura
        self.eye_height = int(self.eye_width + 5)  # 12% da altura
        self.pupil_size = int(self.eye_width * 0.4)  # 40% do olho
        self.eye_spacing = int(self.screen_w * 0.62)  # 25% da largura

        # Redefine o centro com base no tamanho da tela
        self.center_x = self.screen_w // 2 - 3
        self.center_y = self.screen_h // 2 + 10

        self.canvas = tk.Canvas(self, width=self.winfo_screenwidth(), height=self.winfo_screenheight(), bg="black",
                                highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.handle_touch)  # Toque/cliqu

        self.after(100, self.deiconify)
        self.after(150, self.focus_force)

        # Elementos dos olhos
        self.left_eye = None
        self.right_eye = None
        self.left_pupil = None
        self.right_pupil = None
        self.left_highlight = None
        self.right_highlight = None
        self.left_eyelid = None
        self.right_eyelid = None

        # Expressões disponíveis
        self.expressions = {
            "Neutro": self.neutral_eyes,
            "Feliz": self.happy_eyes,
            "Triste": self.sad_eyes,
            "Bravo": self.angry_eyes,
            "Surpreso": self.surprised_eyes,
            "Dormindo": self.sleepy_eyes,
            "Piscando": self.blink_animation,
            "Travesso": self.playful_eyes
        }

        self.current_expression = "Neutro"
        self.animation_running = False

        # Controles
        # self.setup_controls()
        # self.draw_eyes()
        self.after(100, self.draw_eyes())

        self.auto_blink()
        self.natural_movement()
        # self.random_movement()
        # self.sad_eyes()
        # self.random_expression_loop()
        # self.look("left")

    def setup_controls(self):
        control_frame = tk.Frame(self, bg="black")
        control_frame.pack(pady=10)

        for expr in self.expressions:
            btn = tk.Button(
                control_frame, text=expr,
                command=lambda e=expr: self.set_expression(e),
                bg="#333", fg="white", relief="flat"
            )
            btn.pack(side="left", padx=5)

    def handle_touch(self, event):
        """Reage ao toque na tela"""
        # Fecha após 2 toques rápidos (double-tap)
        if hasattr(self, 'last_touch_time'):
            if (event.time - self.last_touch_time) < 300:  # 300ms
                self.destroy()
                return

        self.last_touch_time = event.time

    def draw_eyes(self):
        self.canvas.delete("all")
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        # Desenha a base dos olhos
        self.left_eye = self.canvas.create_oval(
            x_left - self.eye_width, self.center_y - self.eye_height,
            x_left + self.eye_width, self.center_y + self.eye_height,
            fill=self.eye_color, outline="#2d7c9d", width=2
        )

        self.right_eye = self.canvas.create_oval(
            x_right - self.eye_width, self.center_y - self.eye_height,
            x_right + self.eye_width, self.center_y + self.eye_height,
            fill=self.eye_color, outline="#2d7c9d", width=2
        )

        # Desenha as pupilas
        self.left_pupil = self.canvas.create_oval(
            x_left - self.pupil_size, self.center_y - self.pupil_size,
            x_left + self.pupil_size, self.center_y + self.pupil_size,
            fill=self.pupil_color, outline=""
        )

        self.right_pupil = self.canvas.create_oval(
            x_right - self.pupil_size, self.center_y - self.pupil_size,
            x_right + self.pupil_size, self.center_y + self.pupil_size,
            fill=self.pupil_color, outline=""
        )

        # Reflexos nos olhos
        self.left_highlight = [
            self.canvas.create_oval(
                x_left + 15, self.center_y - 15,
                x_left + 5, self.center_y - 5,
                fill=self.highlight_color, outline=""
            )
        ]

        self.right_highlight = [
            self.canvas.create_oval(
                x_right + 15, self.center_y - 15,
                x_right + 5, self.center_y - 5,
                fill=self.highlight_color, outline=""
            )
        ]

        # Pálpebras (inicialmente invisíveis)
        self.left_eyelid_top = self.canvas.create_rectangle(0, 0, 0, 0, fill="black", outline="")
        self.left_eyelid_bottom = self.canvas.create_rectangle(0, 0, 0, 0, fill="black", outline="")
        self.right_eyelid_top = self.canvas.create_rectangle(0, 0, 0, 0, fill="black", outline="")
        self.right_eyelid_bottom = self.canvas.create_rectangle(0, 0, 0, 0, fill="black", outline="")

        # Aplica a expressão atual
        self.expressions[self.current_expression]()

    def set_expression(self, expression):
        if not self.animation_running:
            self.current_expression = expression

            # Salva as posições atuais
            self.start_coords = {
                "left_eye": self.canvas.coords(self.left_eye),
                "right_eye": self.canvas.coords(self.right_eye),
                "left_pupil": self.canvas.coords(self.left_pupil),
                "right_pupil": self.canvas.coords(self.right_pupil),
            }

            # Define as coordenadas alvo chamando a expressão
            self.expressions[expression]()
            self.target_coords = {
                "left_eye": self.canvas.coords(self.left_eye),
                "right_eye": self.canvas.coords(self.right_eye),
                "left_pupil": self.canvas.coords(self.left_pupil),
                "right_pupil": self.canvas.coords(self.right_pupil),
            }

            # Restaura as posições iniciais para começar a interpolação
            self.canvas.coords(self.left_eye, *self.start_coords["left_eye"])
            self.canvas.coords(self.right_eye, *self.start_coords["right_eye"])
            self.canvas.coords(self.left_pupil, *self.start_coords["left_pupil"])
            self.canvas.coords(self.right_pupil, *self.start_coords["right_pupil"])

            self.animate_expression_change()

    def animate_expression_change(self):
        self.animation_running = True
        steps = 10
        delay = 30

        def step(i):
            if i <= steps:
                fraction = i / steps
                self.apply_expression_interpolation(fraction)
                self.after(delay, step, i + 1)
            else:
                self.animation_running = False

        step(0)

    def apply_expression_interpolation(self, fraction):
        def interpolate(start, end):
            return [s + (e - s) * fraction for s, e in zip(start, end)]

        left_eye_coords = interpolate(self.start_coords["left_eye"], self.target_coords["left_eye"])
        right_eye_coords = interpolate(self.start_coords["right_eye"], self.target_coords["right_eye"])
        left_pupil_coords = interpolate(self.start_coords["left_pupil"], self.target_coords["left_pupil"])
        right_pupil_coords = interpolate(self.start_coords["right_pupil"], self.target_coords["right_pupil"])

        self.canvas.coords(self.left_eye, *left_eye_coords)
        self.canvas.coords(self.right_eye, *right_eye_coords)
        self.canvas.coords(self.left_pupil, *left_pupil_coords)
        self.canvas.coords(self.right_pupil, *right_pupil_coords)

    def look(self, direction, duration=0.3, move_amount=40):
        """Move os olhos de forma suave e realista para uma direção"""
        if self.animation_running:
            return

        self.animation_running = True

        # Configurações de movimento
        steps = int(duration * 1000 / 20)  # calcula steps baseado na duração
        current_step = 0

        # Posições atuais das pupilas
        left_coords = self.canvas.coords(self.left_pupil)
        right_coords = self.canvas.coords(self.right_pupil)

        current_left_x = (left_coords[0] + left_coords[2]) / 2
        current_left_y = (left_coords[1] + left_coords[3]) / 2
        current_right_x = (right_coords[0] + right_coords[2]) / 2
        current_right_y = (right_coords[1] + right_coords[3]) / 2

        # Posições dos centros dos olhos
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        # Alvos baseados na direção
        if direction == "left":
            target_left_x = x_left - move_amount
            target_left_y = self.center_y
            target_right_x = x_right - move_amount
            target_right_y = self.center_y
        elif direction == "right":
            target_left_x = x_left + move_amount
            target_left_y = self.center_y
            target_right_x = x_right + move_amount
            target_right_y = self.center_y
        elif direction == "up":
            target_left_x = x_left
            target_left_y = self.center_y - move_amount
            target_right_x = x_right
            target_right_y = self.center_y - move_amount
        elif direction == "down":
            target_left_x = x_left
            target_left_y = self.center_y + move_amount
            target_right_x = x_right
            target_right_y = self.center_y + move_amount
        elif direction == "center":
            target_left_x = x_left
            target_left_y = self.center_y
            target_right_x = x_right
            target_right_y = self.center_y
        elif direction == "random":
            # Movimento natural - olhos não se movem exatamente na mesma direção
            angle = random.uniform(0, 2 * math.pi)
            offset_x = move_amount * math.cos(angle)
            offset_y = move_amount * math.sin(angle) * 0.7  # movimento vertical mais limitado

            target_left_x = x_left + offset_x * 0.8  # olho esquerdo move um pouco menos
            target_left_y = self.center_y + offset_y
            target_right_x = x_right + offset_x
            target_right_y = self.center_y + offset_y
        else:
            self.animation_running = False
            return

        def animate():
            nonlocal current_step

            if current_step <= steps:
                # Interpolação suave (ease-out)
                t = current_step / steps
                t = 1 - (1 - t) ** 2  # aplica easing

                # Calcula posições intermediárias
                new_left_x = current_left_x + (target_left_x - current_left_x) * t
                new_left_y = current_left_y + (target_left_y - current_left_y) * t
                new_right_x = current_right_x + (target_right_x - current_right_x) * t
                new_right_y = current_right_y + (target_right_y - current_right_y) * t

                # Atualiza pupilas
                self.canvas.coords(self.left_pupil,
                                   new_left_x - self.pupil_size, new_left_y - self.pupil_size,
                                   new_left_x + self.pupil_size, new_left_y + self.pupil_size)
                self.canvas.coords(self.right_pupil,
                                   new_right_x - self.pupil_size, new_right_y - self.pupil_size,
                                   new_right_x + self.pupil_size, new_right_y + self.pupil_size)

                # Atualiza reflexos
                for highlight in self.left_highlight:
                    hl_coords = self.canvas.coords(highlight)
                    if hl_coords:
                        dx = new_left_x - x_left
                        dy = new_left_y - self.center_y
                        self.canvas.move(highlight, dx - (hl_coords[0] - x_left - 10),
                                         dy - (hl_coords[1] - self.center_y + 10))

                for highlight in self.right_highlight:
                    hl_coords = self.canvas.coords(highlight)
                    if hl_coords:
                        dx = new_right_x - x_right
                        dy = new_right_y - self.center_y
                        self.canvas.move(highlight, dx - (hl_coords[0] - x_right - 10),
                                         dy - (hl_coords[1] - self.center_y + 10))

                current_step += 1
                self.after(20, animate)
            else:
                self.animation_running = False

        animate()

    # Expressões faciais
    def neutral_eyes(self):
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        # Olhos com formato normal
        self.canvas.coords(self.left_eye,
                           x_left - self.eye_width, self.center_y - self.eye_height,
                           x_left + self.eye_width, self.center_y + self.eye_height)
        self.canvas.coords(self.right_eye,
                           x_right - self.eye_width, self.center_y - self.eye_height,
                           x_right + self.eye_width, self.center_y + self.eye_height)

        # Pupilas centradas
        self.canvas.coords(self.left_pupil,
                           x_left - self.pupil_size, self.center_y - self.pupil_size,
                           x_left + self.pupil_size, self.center_y + self.pupil_size)
        self.canvas.coords(self.right_pupil,
                           x_right - self.pupil_size, self.center_y - self.pupil_size,
                           x_right + self.pupil_size, self.center_y + self.pupil_size)

        # Reflexo também de volta para a posição original
        self.canvas.coords(self.left_highlight[0],
                           x_left + 5, self.center_y - 15,
                           x_left + 15, self.center_y - 5)
        self.canvas.coords(self.right_highlight[0],
                           x_right + 5, self.center_y - 15,
                           x_right + 15, self.center_y - 5)

        # Esconde as pálpebras
        self.canvas.coords(self.left_eyelid_top, 0, 0, 0, 0)
        self.canvas.coords(self.left_eyelid_bottom, 0, 0, 0, 0)
        self.canvas.coords(self.right_eyelid_top, 0, 0, 0, 0)
        self.canvas.coords(self.right_eyelid_bottom, 0, 0, 0, 0)

    def happy_eyes(self):
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        # Olhos mais estreitos (como sorrindo)
        self.canvas.coords(self.left_eye,
                           x_left - self.eye_width, self.center_y - self.eye_height // 2,
                           x_left + self.eye_width, self.center_y + self.eye_height // 2)
        self.canvas.coords(self.right_eye,
                           x_right - self.eye_width, self.center_y - self.eye_height // 2,
                           x_right + self.eye_width, self.center_y + self.eye_height // 2)

        # Pupilas movidas para cima
        self.canvas.coords(self.left_pupil,
                           x_left - 20, self.center_y - 30,
                           x_left + 20, self.center_y + 10)
        self.canvas.coords(self.right_pupil,
                           x_right - 20, self.center_y - 30,
                           x_right + 20, self.center_y + 10)

    def sad_eyes(self):
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        # Olhos mais abertos na parte inferior, simulando olhar triste
        self.canvas.coords(self.left_eye,
                           x_left - self.eye_width // 2, self.center_y - self.eye_height // 3,
                           x_left + self.eye_width // 2, self.center_y + self.eye_height)
        self.canvas.coords(self.right_eye,
                           x_right - self.eye_width // 2, self.center_y - self.eye_height // 3,
                           x_right + self.eye_width // 2, self.center_y + self.eye_height)

        # Pupilas menores e deslocadas levemente para baixo
        pupil_width = 20
        pupil_height = 20
        self.canvas.coords(self.left_pupil,
                           x_left - pupil_width // 2, self.center_y + 10,
                           x_left + pupil_width // 2, self.center_y + 10 + pupil_height)
        self.canvas.coords(self.right_pupil,
                           x_right - pupil_width // 2, self.center_y + 10,
                           x_right + pupil_width // 2, self.center_y + 10 + pupil_height)

        # Pálpebras superiores caídas (linhas diagonais)
        if hasattr(self, 'left_eyelid'):
            self.canvas.delete(self.left_eyelid)
            self.canvas.delete(self.right_eyelid)

        self.left_eyelid = self.canvas.create_line(
            x_left - self.eye_width // 2, self.center_y - self.eye_height // 3,
            x_left + self.eye_width // 2, self.center_y - self.eye_height // 2,
            fill="black", width=2
        )
        self.right_eyelid = self.canvas.create_line(
            x_right - self.eye_width // 2, self.center_y - self.eye_height // 3,
            x_right + self.eye_width // 2, self.center_y - self.eye_height // 2,
            fill="black", width=2
        )

    def angry_eyes(self):
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 22

        # Olhos em diagonal (como sobrancelhas franzidas)
        self.canvas.coords(self.left_eye,
                           x_left - self.eye_width, self.center_y - self.eye_height // 3,
                           x_left + self.eye_width, self.center_y + self.eye_height)
        self.canvas.coords(self.right_eye,
                           x_right - self.eye_width, self.center_y - self.eye_height // 3,
                           x_right + self.eye_width, self.center_y + self.eye_height)

        # Pupilas movidas para o centro
        self.canvas.coords(self.left_pupil,
                           x_left - 15, self.center_y - 10,
                           x_left + 5, self.center_y + 20)
        self.canvas.coords(self.right_pupil,
                           x_right - 5, self.center_y - 10,
                           x_right + 15, self.center_y + 20)

    def surprised_eyes(self):
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        # Olhos bem arredondados
        self.canvas.coords(self.left_eye,
                           x_left - self.eye_width, self.center_y - self.eye_height,
                           x_left + self.eye_width, self.center_y + self.eye_height)
        self.canvas.coords(self.right_eye,
                           x_right - self.eye_width, self.center_y - self.eye_height,
                           x_right + self.eye_width, self.center_y + self.eye_height)

        # Pupilas pequenas e centradas
        self.canvas.coords(self.left_pupil,
                           x_left - 10, self.center_y - 10,
                           x_left + 10, self.center_y + 10)
        self.canvas.coords(self.right_pupil,
                           x_right - 10, self.center_y - 10,
                           x_right + 10, self.center_y + 10)

    def sleepy_eyes(self):
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        # Olhos semi-fechados
        self.canvas.coords(self.left_eye,
                           x_left - self.eye_width, self.center_y - 10,
                           x_left + self.eye_width, self.center_y + 10)
        self.canvas.coords(self.right_eye,
                           x_right - self.eye_width, self.center_y - 10,
                           x_right + self.eye_width, self.center_y + 10)

        # Pupilas quase invisíveis
        self.canvas.coords(self.left_pupil,
                           x_left - 5, self.center_y - 5,
                           x_left + 5, self.center_y + 5)
        self.canvas.coords(self.right_pupil,
                           x_right - 5, self.center_y - 5,
                           x_right + 5, self.center_y + 5)

    def playful_eyes(self):
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        # Olhos assimétricos (um mais aberto que o outro)
        self.canvas.coords(self.left_eye,
                           x_left - self.eye_width, self.center_y - self.eye_height,
                           x_left + self.eye_width, self.center_y + self.eye_height)
        self.canvas.coords(self.right_eye,
                           x_right - self.eye_width, self.center_y - self.eye_height // 2,
                           x_right + self.eye_width, self.center_y + self.eye_height // 2)

        # Pupilas em direções diferentes
        self.canvas.coords(self.left_pupil,
                           x_left - 20, self.center_y - 20,
                           x_left, self.center_y)
        self.canvas.coords(self.right_pupil,
                           x_right, self.center_y,
                           x_right + 20, self.center_y + 20)

    # Animações
    def blink_animation(self):
        if not self.animation_running:
            self.animation_running = True
            steps = 5
            delay = 30

            def close_eyes(i):
                if i <= steps:
                    fraction = i / steps
                    self.update_eyelids(fraction)
                    self.after(delay, close_eyes, i + 1)
                else:
                    self.after(100, open_eyes, steps)

            def open_eyes(i):
                if i >= 0:
                    fraction = i / steps
                    self.update_eyelids(fraction)
                    self.after(delay, open_eyes, i - 1)
                else:
                    self.animation_running = False

            close_eyes(0)

    def update_eyelids(self, fraction):
        margin = 10  # valor ajustável: maior = pálpebras maiores
        # Posições dos centros dos olhos
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        top_height = self.center_y - (self.eye_height + margin) * (1 - fraction)
        bottom_height = self.center_y + (self.eye_height + margin) * (1 - fraction)

        eye_w = self.eye_width + margin

        # LEFT
        self.canvas.coords(self.left_eyelid_top,
                           x_left - eye_w, self.center_y - self.eye_height - margin,
                           x_left + eye_w, top_height)

        self.canvas.coords(self.left_eyelid_bottom,
                           x_left - eye_w, bottom_height,
                           x_left + eye_w, self.center_y + self.eye_height + margin)

        # RIGHT
        self.canvas.coords(self.right_eyelid_top,
                           x_right - eye_w, self.center_y - self.eye_height - margin,
                           x_right + eye_w, top_height)

        self.canvas.coords(self.right_eyelid_bottom,
                           x_right - eye_w, bottom_height,
                           x_right + eye_w, self.center_y + self.eye_height + margin)

    def auto_blink(self):
        self.after(random.randint(3000, 8000), self.auto_blink)
        if not self.animation_running and self.current_expression != "Dormindo":
            self.blink_animation()

    def natural_movement(self):
        """Movimento natural dos olhos quando em repouso"""
        if not self.animation_running and self.current_expression == "Neutro":
            # 80% de chance de fazer um pequeno movimento
            if random.random() < 0.8:
                directions = ["left", "right", "up", "down", "center", "random"]
                self.look(random.choice(directions), duration=random.uniform(0.2, 0.5))

        # Agenda o próximo movimento
        self.after(random.randint(1000, 3000), self.natural_movement)

    def random_movement(self):
        if self.animation_running or self.current_expression != "Neutro":
            self.after(200, self.random_movement)
            return

        dx = random.randint(-10, 10)
        dy = random.randint(-5, 5)

        # Centro dos olhos
        x_left = self.center_x - self.eye_spacing // 2
        x_right = self.center_x + self.eye_spacing // 2

        # Calcula novo centro proposto
        def move_pupil_safe(pupil, eye_center_x, eye_center_y):
            coords = self.canvas.coords(pupil)
            cx = (coords[0] + coords[2]) / 2 + dx
            cy = (coords[1] + coords[3]) / 2 + dy

            max_dx = self.eye_width - self.pupil_size
            max_dy = self.eye_height - self.pupil_size

            if (eye_center_x - max_dx < cx < eye_center_x + max_dx) and (
                    eye_center_y - max_dy < cy < eye_center_y + max_dy):
                self.canvas.move(pupil, dx, dy)
                return True
            return False

        moved_left = move_pupil_safe(self.left_pupil, x_left, self.center_y)
        moved_right = move_pupil_safe(self.right_pupil, x_right, self.center_y)

        if moved_left:
            for highlight in self.left_highlight:
                self.canvas.move(highlight, dx, dy)
        if moved_right:
            for highlight in self.right_highlight:
                self.canvas.move(highlight, dx, dy)

        self.after(2000, self.random_movement)

    def choose_random_expression(self):
        if not self.animation_running:
            expressions = list(self.expressions.keys())
            chosen = random.choice(expressions)
            self.set_expression(chosen)

    def random_expression_loop(self):
        self.choose_random_expression()
        self.after(5000, self.random_expression_loop)


if __name__ == "__main__":
    app = EilikEyes()
    app.mainloop()