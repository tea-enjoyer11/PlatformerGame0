import pygame
from pygame import Surface, Vector2
import moderngl
from array import array
from Scripts.utils import load_image
from Scripts.utils_math import clamp
import os
import numpy as np

if not pygame.get_init():
    pygame.init()

SCREEN_SIZE = Vector2(800, 600)
UNIFORM_LIST_MAXIMUM = 500


def surf_to_texture(surf: pygame.Surface, ctx: moderngl.Context) -> moderngl.Texture:
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
    tex.swizzle = "BGRA"  # defines how channles are mapped
    tex.write(surf.get_view("1"))
    return tex


def load_images(path: str, ctx: moderngl.Context) -> list[moderngl.Context]:
    imgs: list[moderngl.Context] = []
    for img_name in sorted(os.listdir(path)):
        imgs.append(surf_to_texture(load_image(path + "/" + img_name), ctx))
    return imgs


def to_ndc(pos: tuple) -> tuple:
    return (
        (pos[0] / SCREEN_SIZE.x) * 2 - 1,
        1 - (pos[1] / SCREEN_SIZE.y) * 2
    )


vertex_shader = """
#version 330 core

in vec2 vert;
in vec2 texcoords;
out vec2 uvs;

void main() {
uvs = texcoords;
gl_Position = vec4(vert, 0.0, 1.0);
}
"""
fragment_shader = """
#version 330 core

uniform sampler2D tex;

in vec2 uvs;
out vec4 f_color;

void main() {
f_color = vec4(texture(tex, uvs).rgb,1.0);
}
"""


def gen_quad(pos: Vector2, size: Vector2, ctx: moderngl.Context) -> moderngl.Buffer:
    x, y = pos.x, pos.y
    w, h = size.x, size.y

    ndc_x = (x / SCREEN_SIZE.x) * 2  # -1
    ndc_y = (y / SCREEN_SIZE.y) * 2  # -1
    ndc_width = (w / SCREEN_SIZE.x) * 2
    ndc_height = (h / SCREEN_SIZE.y) * 2

    quad_buffer = ctx.buffer(data=array('f', [
        # x, y, s, t
        ndc_x, ndc_y + ndc_height, 0.0, 1.0,  # top left
        ndc_x + ndc_width, ndc_y, 1.0, 0.0,  # bottom right
        ndc_x, ndc_y, 0.0, 0.0,  # bottom left

        ndc_x, ndc_y + ndc_height, 0.0, 1.0,  # top left
        ndc_x + ndc_width, ndc_y, 1.0, 0.0,  # bottom right
        ndc_x + ndc_width, ndc_y + ndc_height, 1.0, 1.0,  # top right
    ]))
    return quad_buffer


class Renderer:
    def __init__(self) -> None:
        self.ctx = moderngl.create_context(require=330)  # context for rendering in the opengl pipeline

        self.program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

        qauad_buffer = self.ctx.buffer(data=array('f', [
            # x,y (vertex cords), x,y (uv cords)
            # flips the y cord (pygame y axis is flipped)
            -1.0, 1.0, 0.0, 0.0,  # topleft
            1.0, 1.0, 1.0, 0.0,  # topright
            -1.0, -1.0, 0.0, 1.0,  # bottomleft
            1.0, -1.0, 1.0, 1.0,  # bottomright
        ]))
        self.vao1 = self.ctx.vertex_array(self.program, [(qauad_buffer, "2f 2f", "vert", "texcoords")])
        self.texture = surf_to_texture(pygame.image.load("assets/background.png").convert(), self.ctx)

        self.instanced_program = self.ctx.program(
            vertex_shader='''
                #version 330

                in vec2 in_vert;
                in vec4 in_color;

                out vec4 v_color;

                uniform float Rotation;
                uniform vec2 Scale;

                void main() {
                    v_color = in_color;
                    float r = Rotation * (0.5 + gl_InstanceID * 0.05);
                    mat2 rot = mat2(cos(r), sin(r), -sin(r), cos(r));
                    gl_Position = vec4((rot * in_vert) * Scale, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330

                in vec4 v_color;
                out vec4 f_color;

                void main() {
                    f_color = v_color;
                }
            ''',
        )

        vertices = np.array([
            # x, y, red, green, blue, alpha
            1.0, 0.0, 1.0, 0.0, 0.0, 0.5,
            -0.5, 0.86, 0.0, 1.0, 0.0, 0.5,
            -0.5, -0.86, 0.0, 0.0, 1.0, 0.5,
        ], dtype='f4')
        self.vbo = self.ctx.buffer(vertices)
        self.vao2 = self.ctx.vertex_array(
            self.instanced_program,
            [(self.vbo, '2f 4f', 'in_vert', 'in_color')],
        )

        self.instanced_program_particles = self.ctx.program(
            vertex_shader='''
                #version 330

                in vec2 in_vert;
                in vec2 texcoords;

                out vec2 uvs;
                flat out int instance_state;

                uniform vec2[500] positions;
                uniform int[500] states;
                

                void main() {
                    uvs = texcoords;
                    instance_state = states[gl_InstanceID];
                    vec2 offset = positions[gl_InstanceID];
                    
                    gl_Position = vec4(in_vert + offset, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330

                in vec2 uvs;
                flat in int instance_state;
                out vec4 f_color;

                uniform sampler2D[4] images;

                void main() {
                    f_color = texture(images[instance_state], uvs).rgba;
                    f_color = vec4(uvs, f_color.b, 1.0);
                }
            ''',
        )
        vertices = np.array([
            # x,y (vertex cords), x,y (uv cords)
            # flips the y cord (pygame y axis is flipped)
            -1.0, 1.0, 0.0, 0.0,  # topleft
            1.0, 1.0, 1.0, 0.0,  # topright
            -1.0, -1.0, 0.0, 1.0,  # bottomleft
            1.0, -1.0, 1.0, 1.0,  # bottomright
        ], dtype='f')
        self.vbo2 = self.ctx.buffer(vertices)
        self.vbo2 = gen_quad(Vector2(0), Vector2(16, 16), self.ctx)
        self.vao3 = self.ctx.vertex_array(
            self.instanced_program_particles,
            [(self.vbo2, '2f 2f', 'in_vert', 'texcoords')],
        )
        self.particle_cache = {
            "particle": load_images("assets/particles/particle", self.ctx),
            "leaf": load_images("assets/particles/leaf", self.ctx)
        }

    def render(self, surface: Surface) -> None:
        self.ctx.clear(1.0, 1.0, 1.0)
        self.ctx.enable(moderngl.BLEND)

        frame_tex = surf_to_texture(surface, self.ctx)
        frame_tex.use(0)
        self.program["tex"] = 0
        self.vao1.render(mode=moderngl.TRIANGLE_STRIP)
        frame_tex.release()

        # self.instanced_program["Scale"] = (0.5, (800 / 600) * 0.5)
        # self.instanced_program["Rotation"] = 0.5
        # # For every instanced rendered gl_InstanceID increments by 1
        # self.vao2.render(instances=100)

    def render_particles(self, particles: list) -> None:
        pos = []
        states = []

        for i, p in enumerate(particles):
            x, y = p.pos
            pos.append(to_ndc((x, y)))
            states.append(int(p.state))

        l_pos = len(pos)
        if l_pos < UNIFORM_LIST_MAXIMUM:
            diff = UNIFORM_LIST_MAXIMUM - l_pos
            for _ in range(diff):
                pos.append((0, 0))
        elif l_pos > UNIFORM_LIST_MAXIMUM:
            diff = l_pos - UNIFORM_LIST_MAXIMUM
            for _ in range(diff):
                pos.pop()

        l_states = len(states)
        if l_states < UNIFORM_LIST_MAXIMUM:
            diff = UNIFORM_LIST_MAXIMUM - l_states
            for _ in range(diff):
                states.append(0)
        elif l_states > UNIFORM_LIST_MAXIMUM:
            diff = l_states - UNIFORM_LIST_MAXIMUM
            for _ in range(diff):
                states.pop()

        # print(pos)
        # for pair in pos:
        #     print("pair:", pair)
        #     for cord in pair:
        #         print(pair, cord)

        # self.instanced_program_particles["positions"] = pos
        self.instanced_program_particles["positions"].write(array('f', [coord for pair in pos for coord in pair]))
        # self.instanced_program_particles["states"] = states
        self.instanced_program_particles["states"].write(array('i', states))

        for i, img in enumerate(self.particle_cache["particle"]):
            img.use(i)
        self.instanced_program_particles['images'] = [i for i in range(len(self.particle_cache["particle"]))]
        # self.instanced_program_particles["images"] = imgs

        self.vao3.render(mode=moderngl.TRIANGLE_STRIP, instances=clamp(0, len(particles), UNIFORM_LIST_MAXIMUM))

    def quit(self) -> None:
        self.texture.release()
