import pygame
from pygame import Surface, Vector2
import moderngl
from array import array
import math
from Scripts.utils import load_image
import os

if not pygame.get_init():
    pygame.init()


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


def point_to_uv(p: Vector2) -> tuple:
    return (p[0] / 800, 1 - (p[1] / 600))  # 800, 600 = SCREEN_SIZE


def from_uv(pos: Vector2):
    ...


def gen_particle_sheet(path: str) -> Surface:
    imgs: list[Surface] = []
    for img_name in sorted(os.listdir(path)):
        imgs.append(load_image(path + "/" + img_name))
    size = Vector2(imgs[0].get_size())
    amount = len(imgs)
    final_surf = Surface((size.x, size.y * amount))
    for i, img in enumerate(imgs):
        final_surf.blit(img, (0, i * size.y))
    return final_surf


def gen_quad(pixel_size: Vector2, ctx: moderngl.Context) -> moderngl.Buffer:
    screen_size = Vector2(800, 600)
    ndc_size = Vector2(
        pixel_size.x / screen_size.x * 2,  # multiply by 2 because NDC range is -1 to 1
        pixel_size.y / screen_size.y * 2
    )

    quad_buffer = ctx.buffer(data=array('f', [
        -ndc_size.x / 2, ndc_size.y / 2, 0.0, 0.0,  # topleft
        ndc_size.x / 2, ndc_size.y / 2, 1.0, 0.0,  # topright
        -ndc_size.x / 2, -ndc_size.y / 2, 0.0, 1.0,  # bottomleft
        ndc_size.x / 2, -ndc_size.y / 2, 1.0, 1.0,  # bottomright
    ]))
    return quad_buffer


class Renderer:
    def __init__(self) -> None:
        self.ctx = moderngl.create_context(require=330)  # context for rendering in the opengl pipeline

        vertex_shader = """#version 330 core

in vec2 vert;
in vec2 texcoords;
out vec2 uvs;

void main() {
    uvs = texcoords;
    gl_Position = vec4(vert, 0.0, 1.0);
}
"""
        vertex_shader_instanced = """#version 330 core

in vec2 vert;
in vec2 texcoords;
out vec2 uvs;

uniform vec2 position;

void main() {
    uvs = texcoords;
    vec2 offset = vec2(0);
    gl_Position = vec4(vert + offset, 0.0, 1.0);
}
"""
        fragment_shader = """#version 330 core

uniform sampler2D tex;

in vec2 uvs;
out vec4 f_color;

void main() {
    f_color = vec4(texture(tex, uvs).rgb,1.0);
}
"""
        fragment_shader_instanced = """#version 330 core

uniform sampler2D tex;

in vec2 uvs;
out vec4 f_color;

void main() {
    f_color = vec4(texture(tex, uvs).rgba);
}
"""
        self.program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        self.program_instanced = self.ctx.program(vertex_shader=vertex_shader_instanced, fragment_shader=fragment_shader_instanced)

        qauad_buffer = self.ctx.buffer(data=array('f', [
            # x,y (vertex cords), x,y (uv cords)
            # flips the y cord (pygame y axis is flipped)
            -1.0, 1.0, 0.0, 0.0,  # topleft
            1.0, 1.0, 1.0, 0.0,  # topright
            -1.0, -1.0, 0.0, 1.0,  # bottomleft
            1.0, -1.0, 1.0, 1.0,  # bottomright
        ]))
        particle_quad_buffer = gen_quad(Vector2(16, 16), self.ctx)
        self.vao1 = self.ctx.vertex_array(self.program, [(qauad_buffer, "2f 2f", "vert", "texcoords")])
        self.vao2 = self.ctx.vertex_array(self.program_instanced, [(particle_quad_buffer, "2f 2f", "vert", "texcoords")])

        # self.particle_cache = {
        #     "particle": surf_to_texture(gen_particle_sheet("assets/particles/particle")),
        #     "leaf": surf_to_texture(gen_particle_sheet("assets/particles/leaf"))
        # }
        self.particle_cache = {
            "particle": load_images("assets/particles/particle", self.ctx),
            "leaf": load_images("assets/particles/leaf", self.ctx)
        }

    def render(self, surface: Surface) -> None:
        frame_tex = surf_to_texture(surface, self.ctx)
        frame_tex.use(0)
        self.program["tex"] = 0
        self.vao1.render(mode=moderngl.TRIANGLE_STRIP)

        frame_tex.release()

    def render_particles(self, particles: list) -> None:
        particles = sorted(particles, key=lambda p: p.type)
        for p in particles:
            # print(p, vars(p))
            tex = self.particle_cache[p.type][int(p.state)]
            tex.use(0)
            self.program_instanced["tex"] = 0
            # self.program_instanced["position"] = point_to_uv(p.pos)
            # for name in self.program_instanced:
            #     print(name)
            # self.program_instanced["p_pos"].value = point_to_uv(p.pos)
            self.vao2.render(moderngl.TRIANGLE_STRIP)

    def quit(self) -> None:
        for n, l in self.particle_cache.items():
            print(len(l))
            for t in l:
                print(t)
                t.release()
