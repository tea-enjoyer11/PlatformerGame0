from PIL import Image
import pygame
from pygame import Surface, Vector2
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader, ShaderProgram
import os
import math
from Scripts.utils import load_image
import numpy as np


SCREEN_SIZE = Vector2(800, 600)


vertex_shader = """#version 330 core

in vec2 aPos;
in vec2 texcoords;
out vec2 uvs;

void main() {
    uvs = texcoords;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
"""

fragment_shader = """#version 330 core

uniform sampler2D tex;

in vec2 uvs;
out vec4 f_color;

void main() {
    f_color = vec4(uvs, 0.63, 1.0);
    f_color = vec4(uvs, 0.0, 1.0);
    vec2 flipped_uv = vec2(uvs.x, uvs.y * -1);
    f_color = vec4(texture(tex, flipped_uv).rgb,1.0);
}
"""


def create_shader(vertex_file_path: str, fragment_file_path: str) -> ShaderProgram:
    # with open(vertex_file_path, "r") as f:
    #     vertex_src = f.readlines()
    vertex_src = vertex_file_path

    # with open(fragment_file_path, "r") as f:
    #     fragment_src = f.readlines()
    fragment_src = fragment_file_path

    shader = compileProgram(
        compileShader(vertex_src, GL_VERTEX_SHADER),
        compileShader(fragment_src, GL_FRAGMENT_SHADER)
    )

    success = glGetProgramiv(shader, GL_LINK_STATUS)
    if not success:
        info_log = glGetProgramInfoLog(shader)
        raise RuntimeError(f"Shader program failed to compile: {info_log}")

    return shader


def make_quad(pos: Vector2, size: Vector2) -> np.array:
    x, y = pos.x, pos.y
    w, h = size.x, size.y

    ndc_x = (x / SCREEN_SIZE.x) * 2 - 1
    ndc_y = (y / SCREEN_SIZE.y) * 2 - 1
    ndc_width = (w / SCREEN_SIZE.x) * 2
    ndc_height = (h / SCREEN_SIZE.y) * 2

    quad_buffer = np.array(
        object=[
            # x, y, s, t
            ndc_x, ndc_y + ndc_height, 0.0, 1.0,  # top left
            ndc_x + ndc_width, ndc_y, 1.0, 0.0,  # bottom right
            ndc_x, ndc_y, 0.0, 0.0,  # bottom left

            ndc_x, ndc_y + ndc_height, 0.0, 1.0,  # top left
            ndc_x + ndc_width, ndc_y, 1.0, 0.0,  # bottom right
            ndc_x + ndc_width, ndc_y + ndc_height, 1.0, 1.0,  # top right
            # -1.0, 1.0, 0.0, 1.0,
            # 1.0, -1.0, 1.0, 0.0,
            # -1.0, -1.0, 0.0, 0.0,

            # -1.0, -1.0, 0.0, 1.0,
            # 1.0, 1.0, 1.0, 0.0,
            # 1.0, 1.0, 1.0, 1.0

            # -1.0, 0.5, 0.0, 0.0,
            # 0.5, 0.5, 1.0, 0.0,
            # 0.5, -0.5, 0.0, 1.0,
            # -0.5, -0.5, 1.0, 1.0
            # 0.5, 0.5, 0.0, 1.0,  # top right
            # 0.5, -0.5, 0.0, 0.0,  # bottom right
            # -0.5, -0.5, 0.0, 1.0,  # bottom left
            # -0.5, 0.5, 1.0, 1.0  # top left
        ],
        dtype=np.float32
    )
    print(quad_buffer)
    indices = np.array(
        [
            0, 1, 3,
            1, 2, 3
        ],
        dtype=np.float32
    )
    return quad_buffer, indices


class Renderer:
    def __init__(self) -> None:
        # glViewport(-int(SCREEN_SIZE.x) // 4, -int(SCREEN_SIZE.y) // 4, int(SCREEN_SIZE.x), int(SCREEN_SIZE.y))

        glClearColor(0.1, 0.2, 0.2, 1)

        self.screen = RectMesh(Vector2(0, 0), SCREEN_SIZE)  # nicht der eigentliche screen, sonder das mesh für den screen
        self.shader = Shader(vertex_shader, fragment_shader)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def render(self, surface: Surface) -> None:
        glClear(GL_COLOR_BUFFER_BIT)

        # t = Texture("assets/background.png")
        t = TextureSurface(surface, SCREEN_SIZE)

        self.shader.use()
        t.use()
        # glUniform1i(glGetUniformLocation(self.shader.program, "tex"), self.t.texture)
        self.screen.bind()
        self.screen.draw()
        pygame.display.flip()
        # print(vars(t))
        t.destroy()


class Texture:
    def __init__(self, filepath: str, size: Vector2 | None = None) -> None:
        self.texture = glGenTextures(1)  # make space in memory for texture
        glBindTexture(GL_TEXTURE_2D, self.texture)  # binding that as our current texture
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)  # s=0: left side, s=1 right side of texture
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)  # t=0: top side, t=1 bottom side of texture
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)  # minifiying texture (downscaling)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)  # magnifiying texture (upscaling)
        with Image.open(filepath, "r") as image:
            if size:
                image_width, image_height = image.size
            else:
                image_width, image_height = size.x, size.y
            image = image.convert("RGB")
            image_data = image.tobytes()
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image_width, image_height, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)
        glGenerateMipmap(GL_TEXTURE_2D)

    def use(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def destroy(self):
        glDeleteTextures(1, (self.texture,))


class TextureSurface:
    def __init__(self, surface: Surface, size: Vector2 | None = None) -> None:
        self.texture = glGenTextures(1)

        raw_surface = pygame.image.tostring(surface, "RGBA")
        glBindTexture(GL_TEXTURE_2D, self.texture)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

        surface_rect = surface.get_rect()
        if size:
            image_width, image_height = surface_rect.w, surface_rect.h
        else:
            image_width, image_height = size.x, size.y
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw_surface)
        glGenerateMipmap(GL_TEXTURE_2D)

    def use(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def destroy(self):
        glDeleteTextures(1, (self.texture,))


class Mesh:
    def __init__(self) -> None:
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        stride = 4 * 4  # bytes per vertex. Here its 4 floats (a float = 4 bytes)
        offset = 0

        # position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
        offset += 2 * 4
        # texture
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))

        self.vertex_count = 0  # wird in children gesetzt

    def bind(self) -> None:
        glBindVertexArray(self.vao)

    def draw(self) -> None:
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)

        # glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        # glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, 0)


def destroy(self):
    glDeleteVertexArrays(1, (self.vao,))
    glDeleteBuffers(1, (self.vbo, self.ebo))


class RectMesh(Mesh):
    def __init__(self, pos: Vector2, size: Vector2) -> None:
        super().__init__()

        vertices, indices = make_quad(pos, size)
        self.vertex_count = 6

        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)


class Shader:
    __slots__ = ("program", "single_uniforms", "multi_uniforms")

    def __init__(self, vertex_path: str, fragment_path: str) -> None:

        self.program = create_shader(vertex_path, fragment_path)

        self.single_uniforms: dict[int, int] = {}
        self.multi_uniforms: dict[int, list[int]] = {}

    def cache_single_cache_location(self, uniform_type: int, uniform_name: str) -> None:
        self.single_uniforms[uniform_type] = glGetUniformLocation(self.program, uniform_name)

    def cache_multiple_cache_location(self, uniform_type: int, uniform_name: str) -> None:
        if uniform_type not in self.multi_uniforms:
            self.multi_uniforms[uniform_type] = []

        self.multi_uniforms[uniform_type].append(
            glGetUniformLocation(
                self.program, uniform_name)
        )

    def fetch_single_location(self, uniform_type: int) -> int:
        return self.single_uniforms[uniform_type]

    def fetch_multi_location(self, uniform_type: int, index: int) -> int:
        return self.multi_uniforms[uniform_type][index]

    def use(self) -> None:
        glUseProgram(self.program)

    def destroy(self) -> None:
        glDeleteProgram(self.program)
